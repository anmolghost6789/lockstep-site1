#!/usr/bin/env python3
"""Deterministic local runtime for the DE Discovery Claude Code plugin."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ModuleNotFoundError:
    requirements = Path(__file__).with_name("requirements.txt")
    print(
        json.dumps(
            {
                "error": "Missing required dependency PyYAML",
                "install": f'{sys.executable} -m pip install -r "{requirements}"',
                "type": "MissingDependency",
            },
            indent=2,
        )
    )
    raise SystemExit(1)

from de_discovery_lib import __version__
from de_discovery_lib.actions import authorize
from de_discovery_lib.config import (
    DEFAULT_CONFIG,
    load_config,
    required_facets,
    validate_config,
)
from de_discovery_lib.evidence import discover_files, ingest_file
from de_discovery_lib.io import (
    DiscoveryError,
    RuntimePaths,
    atomic_write_text,
    atomic_write_yaml,
    utc_now,
)
from de_discovery_lib.ingestion import export_ingestion_spec
from de_discovery_lib.okf import (
    impacted_concepts,
    load_concepts,
    rebuild_index,
    validate_bundle,
)
from de_discovery_lib.research import validate_web_source
from de_discovery_lib.scoring import score_candidates
from de_discovery_lib.security import scan_text
from de_discovery_lib.state import (
    load_state,
    record_resource,
    review_source,
    save_state,
    set_phase,
)


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def _paths(args: argparse.Namespace, *, require_config: bool = True) -> RuntimePaths:
    return RuntimePaths.resolve(
        args.project_root,
        getattr(args, "config", ".de-discovery.yaml"),
        require_config=require_config,
    )


def _config_and_state(args: argparse.Namespace) -> tuple[RuntimePaths, dict[str, Any], dict[str, Any]]:
    paths = _paths(args)
    config = load_config(paths.config_path)
    state = load_state(paths.state_path, config["project_id"])
    return paths, config, state


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_doctor(args: argparse.Namespace) -> int:
    paths = _paths(args, require_config=False)
    dependencies = {
        "yaml": importlib.util.find_spec("yaml") is not None,
        "pypdf": importlib.util.find_spec("pypdf") is not None,
        "openpyxl": importlib.util.find_spec("openpyxl") is not None,
    }
    databricks_path = shutil.which("databricks")
    databricks_version = None
    databricks_error = None
    if databricks_path:
        try:
            result = subprocess.run(
                [databricks_path, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            databricks_version = (result.stdout or result.stderr).strip() or None
            if result.returncode:
                databricks_error = f"version command exited {result.returncode}"
        except (OSError, subprocess.TimeoutExpired) as exc:
            databricks_error = type(exc).__name__

    config_result: dict[str, Any] = {"exists": paths.config_path.exists()}
    if paths.config_path.exists():
        try:
            config = load_config(paths.config_path)
            config_result.update(
                {
                    "valid": True,
                    "project_id": config["project_id"],
                    "provider": config["databricks"]["provider"],
                    "research_mode": config["research"]["mode"],
                    "engagement_archetypes": config["engagement"]["archetypes"],
                    "required_facets": sorted(required_facets(config)),
                }
            )
        except DiscoveryError as exc:
            config_result.update({"valid": False, "error": str(exc)})

    report = {
        "plugin_version": __version__,
        "python": sys.version.split()[0],
        "project_root": str(paths.project_root),
        "config": config_result,
        "dependencies": dependencies,
        "databricks_cli": {
            "available": bool(databricks_path),
            "path": databricks_path,
            "version": databricks_version,
            "error": databricks_error,
        },
        "ai_dev_kit_mcp": {
            "available": "inspect Claude runtime tools",
            "reason": "MCP capability is owned by the active Claude session, not this local process",
        },
        "web_research": {
            "available": "inspect Claude runtime tools for WebSearch and WebFetch",
            "reason": "Web tool capability and permissions are owned by the active Claude session",
        },
        "offline_discovery_available": dependencies["yaml"],
    }
    _print(report)
    return 0 if dependencies["yaml"] else 1


def command_init(args: argparse.Namespace) -> int:
    paths = _paths(args, require_config=False)
    if paths.config_path.exists():
        config = load_config(paths.config_path)
    else:
        if not args.project_id or not args.objective:
            raise DiscoveryError(
                "Config is absent; --project-id and --objective are required to initialize it"
            )
        config = deepcopy(DEFAULT_CONFIG)
        config["project_id"] = args.project_id
        config["objective"] = args.objective
        config["readiness_target"] = args.readiness_target
        config["knowledge_root"] = args.knowledge_root
        validate_config(config)
        atomic_write_yaml(paths.config_path, config)
        paths = _paths(args)

    if not config["project_id"].strip() or config["project_id"] == "replace-me":
        raise DiscoveryError("Set a real project_id before initialization")
    if not config["objective"].strip() or config["objective"].startswith("Replace with"):
        raise DiscoveryError("Set the discovery objective before initialization")

    paths.runtime_root.mkdir(parents=True, exist_ok=True)
    (paths.evidence_root / "sha256").mkdir(parents=True, exist_ok=True)
    (paths.evidence_root / "derived").mkdir(parents=True, exist_ok=True)
    paths.reports_root.mkdir(parents=True, exist_ok=True)
    paths.knowledge_root.mkdir(parents=True, exist_ok=True)

    state = load_state(paths.state_path, config["project_id"])
    save_state(paths.state_path, state)
    index = paths.knowledge_root / "index.md"
    log = paths.knowledge_root / "log.md"
    if not index.exists():
        atomic_write_text(
            index,
            (
                "---\n"
                'okf_version: "0.2"\n'
                "---\n\n"
                "# Knowledge index\n\n"
                "_Discovery has been initialized; concepts have not been synthesized yet._\n"
            ),
        )
    if not log.exists():
        atomic_write_text(log, "# Knowledge log\n\n")

    _print(
        {
            "initialized": True,
            "project_id": config["project_id"],
            "config": str(paths.config_path),
            "state": str(paths.state_path),
            "knowledge_root": str(paths.knowledge_root),
            "evidence_mode": config["inputs"]["evidence_mode"],
        }
    )
    return 0


def command_ingest(args: argparse.Namespace) -> int:
    paths, config, state = _config_and_state(args)
    inputs = [Path(item) for item in args.path]
    files: list[Path] = []
    for input_path in inputs:
        files.extend(
            discover_files(
                input_path,
                project_root=paths.project_root,
                knowledge_root=paths.knowledge_root,
                max_files=config["inputs"]["max_files"],
            )
        )
    unique_files = list(dict.fromkeys(files))
    if len(unique_files) > config["inputs"]["max_files"]:
        raise DiscoveryError(
            f"Combined inputs exceed configured max_files={config['inputs']['max_files']}"
        )

    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for source in unique_files:
        try:
            item = ingest_file(source, paths=paths, config=config, state=state)
            item["impacted_concepts"] = impacted_concepts(
                paths.knowledge_root,
                item.get("previous_revision_id"),
            )
            results.append(item)
        except (DiscoveryError, OSError, ValueError) as exc:
            failures.append({"path": str(source), "error": str(exc)})

    output = {
        "ingested": len(results),
        "new": sum(item["status"] == "new" for item in results),
        "changed": sum(item["status"] == "changed" for item in results),
        "unchanged": sum(item["status"] == "unchanged" for item in results),
        "results": results,
        "failures": failures,
    }
    _print(output)
    return 1 if failures else 0


def command_register_observation(args: argparse.Namespace) -> int:
    from urllib.parse import urlsplit

    paths, config, state = _config_and_state(args)
    if scan_text(args.source_uri):
        raise DiscoveryError("Observation source URI appears to contain a secret")
    web_hostname = None
    if args.kind == "web":
        if not args.publisher or not args.applicability:
            raise DiscoveryError(
                "Web observations require --publisher and --applicability"
            )
        web_hostname = validate_web_source(args.source_uri, config["research"])
    if "://" in args.source_uri:
        parsed = urlsplit(args.source_uri)
        if parsed.username or parsed.password:
            raise DiscoveryError("Observation source URI must not contain embedded credentials")
    item = ingest_file(
        Path(args.content_file),
        paths=paths,
        config=config,
        state=state,
    )
    revision_id = item["revision_id"]
    for source in state["sources"].values():
        revision = next(
            (
                entry
                for entry in source.get("revisions", [])
                if entry.get("id") == revision_id
            ),
            None,
        )
        if revision:
            existing_uri = revision.get("source_uri")
            if existing_uri and existing_uri != args.source_uri:
                raise DiscoveryError(
                    "Observation content is already registered with different provenance; "
                    "create a distinct observation note"
                )
            revision.update(
                {
                    "observation_kind": args.kind,
                    "observation_title": args.title,
                    "source_uri": args.source_uri,
                    "observed_at": utc_now(),
                }
            )
            if args.kind == "web":
                revision.update(
                    {
                        "publisher": args.publisher,
                        "applicability": args.applicability,
                        "source_domain": web_hostname,
                    }
                )
            save_state(paths.state_path, state)
            break
    item["impacted_concepts"] = impacted_concepts(
        paths.knowledge_root,
        item.get("previous_revision_id"),
    )
    _print({"registered": True, "observation": item})
    return 0


def command_status(args: argparse.Namespace) -> int:
    paths, config, state = _config_and_state(args)
    changes: list[dict[str, str]] = []
    missing: list[str] = []
    for source in state.get("sources", {}).values():
        logical_path = Path(source["logical_path"])
        if not logical_path.is_file():
            missing.append(str(logical_path))
            continue
        current_id = source.get("current_revision")
        current = next(
            (item for item in source.get("revisions", []) if item.get("id") == current_id),
            None,
        )
        current_digest = _sha256(logical_path)
        if current and current.get("sha256") != current_digest:
            changes.append(
                {
                    "path": str(logical_path),
                    "registered_revision": current_id,
                    "current_sha256": current_digest,
                }
            )
    _print(
        {
            "project_id": config["project_id"],
            "objective": config["objective"],
            "readiness_target": config["readiness_target"],
            "engagement_archetypes": config["engagement"]["archetypes"],
            "required_facets": sorted(required_facets(config)),
            "research_mode": config["research"]["mode"],
            "phase": state.get("phase"),
            "last_completed_step": state.get("last_completed_step"),
            "updated_at": state.get("updated_at"),
            "source_count": len(state.get("sources", {})),
            "changed_sources": changes,
            "missing_sources": missing,
            "open_questions": state.get("open_questions", []),
            "pending_source_revisions": state.get("pending_source_revisions", []),
            "source_reviews": state.get("source_reviews", []),
            "created_resources": state.get("created_resources", []),
            "knowledge_index": str(paths.knowledge_root / "index.md"),
        }
    )
    return 0


def command_authorize(args: argparse.Namespace) -> int:
    _, config, _ = _config_and_state(args)
    result = authorize(
        config,
        action=args.action,
        resource_name=args.resource_name,
        system=args.system,
        catalog=args.catalog,
        schema=args.schema,
    )
    _print(result)
    return {"ALLOW": 0, "ASK": 2, "DENY": 3}[result["decision"]]


def command_record_resource(args: argparse.Namespace) -> int:
    paths, _, state = _config_and_state(args)
    item = record_resource(
        paths.state_path,
        state,
        resource_type=args.type,
        name=args.name,
        resource_uri=args.uri,
        purpose=args.purpose,
    )
    _print({"recorded": True, "resource": item})
    return 0


def command_review_source(args: argparse.Namespace) -> int:
    paths, _, state = _config_and_state(args)
    review = review_source(
        paths.state_path,
        state,
        revision_id=args.revision_id,
        disposition=args.disposition,
        concepts=args.concept or [],
        reason=args.reason,
    )
    _print({"reviewed": True, "source_review": review})
    return 0


def command_record_question(args: argparse.Namespace) -> int:
    paths, _, state = _config_and_state(args)
    questions = state["open_questions"]
    existing = next((item for item in questions if item.get("id") == args.id), None)
    if existing:
        existing.update(
            {
                "question": args.question,
                "owner": args.owner,
                "blocking": args.blocking,
                "status": "open",
                "updated_at": utc_now(),
            }
        )
        item = existing
    else:
        item = {
            "id": args.id,
            "question": args.question,
            "owner": args.owner,
            "blocking": args.blocking,
            "status": "open",
            "created_at": utc_now(),
        }
        questions.append(item)
    save_state(paths.state_path, state)
    _print({"recorded": True, "question": item})
    return 0


def command_resolve_question(args: argparse.Namespace) -> int:
    paths, _, state = _config_and_state(args)
    item = next((item for item in state["open_questions"] if item.get("id") == args.id), None)
    if not item:
        raise DiscoveryError(f"Unknown question id: {args.id}")
    item.update({"status": "resolved", "resolution": args.resolution, "resolved_at": utc_now()})
    save_state(paths.state_path, state)
    _print({"resolved": True, "question": item})
    return 0


def command_rebuild_index(args: argparse.Namespace) -> int:
    paths, _, _ = _config_and_state(args)
    result = rebuild_index(paths)
    _print(result)
    return 0 if result.get("rebuilt") else 1


def command_validate(args: argparse.Namespace) -> int:
    paths, config, state = _config_and_state(args)
    report = validate_bundle(paths, config, state, profile=args.profile)
    _print(report)
    return 0 if report["valid"] else 1


def command_set_phase(args: argparse.Namespace) -> int:
    paths, config, state = _config_and_state(args)
    if args.phase == "complete":
        pending = state.get("pending_source_revisions", [])
        if pending:
            raise DiscoveryError(
                f"Cannot mark complete with {len(pending)} unreviewed source revision(s)"
            )
        open_blockers = [
            item
            for item in state.get("open_questions", [])
            if item.get("status") == "open" and item.get("blocking", True)
        ]
        if open_blockers:
            raise DiscoveryError(
                f"Cannot mark complete with {len(open_blockers)} open blocking question(s)"
            )
        report = validate_bundle(paths, config, state, profile=True)
        if not report["valid"]:
            raise DiscoveryError("Cannot mark complete while OKF profile validation fails")
        if report.get("readiness_result") == "blocked":
            raise DiscoveryError("Cannot mark complete while requested readiness is blocked")
    set_phase(paths.state_path, state, args.phase, args.last_step)
    _print(
        {
            "updated": True,
            "phase": args.phase,
            "last_completed_step": args.last_step,
            "state": str(paths.state_path),
        }
    )
    return 0


def command_score_candidates(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    try:
        value = yaml.safe_load(input_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DiscoveryError(f"Candidate file not found: {input_path}") from exc
    except yaml.YAMLError as exc:
        raise DiscoveryError(f"Invalid candidate YAML: {exc}") from exc
    _print({"candidates": score_candidates(value)})
    return 0


def command_export_ingestion_config(args: argparse.Namespace) -> int:
    paths, config, state = _config_and_state(args)
    report = validate_bundle(paths, config, state, profile=False)
    if not report["valid"]:
        raise DiscoveryError(
            "Cannot export while the OKF bundle is invalid: "
            f"{report['errors'][0]['message']}"
        )
    concepts, parse_errors = load_concepts(paths.knowledge_root)
    if parse_errors:
        raise DiscoveryError(
            f"Cannot export while OKF concepts have parse errors: {parse_errors[0]['message']}"
        )
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = paths.project_root / output
    else:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", args.canonical_id).strip("-")
        safe_name = safe_name or "ingestion-spec"
        output = paths.reports_root / "ingestion-configs" / f"{safe_name}.yaml"
    _print(
        export_ingestion_spec(
            concepts,
            canonical_id=args.canonical_id,
            output=output,
            project_root=paths.project_root,
        )
    )
    return 0


def _add_project_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", default=".", help="Project directory; defaults to cwd")
    parser.add_argument("--config", default=".de-discovery.yaml", help="Project-relative config path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local evidence, state, policy, and OKF runtime for DE Discovery"
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Inspect local discovery capabilities")
    _add_project_args(doctor)
    doctor.set_defaults(handler=command_doctor)

    init = subparsers.add_parser("init", help="Initialize local state and the OKF root")
    _add_project_args(init)
    init.add_argument("--project-id")
    init.add_argument("--objective")
    init.add_argument(
        "--readiness-target",
        choices=("discovery-only", "requirements-ready", "design-ready"),
        default="requirements-ready",
    )
    init.add_argument("--knowledge-root", default="knowledge")
    init.set_defaults(handler=command_init)

    ingest = subparsers.add_parser("ingest", help="Hash, scan, snapshot, and extract evidence")
    _add_project_args(ingest)
    ingest.add_argument("--path", action="append", required=True, help="File or directory; repeatable")
    ingest.set_defaults(handler=command_ingest)

    observation = subparsers.add_parser(
        "register-observation",
        help="Register a redacted interview, web, decision, or Databricks observation",
    )
    _add_project_args(observation)
    observation.add_argument(
        "--kind",
        choices=("databricks", "interview", "web", "decision", "other"),
        required=True,
    )
    observation.add_argument("--title", required=True)
    observation.add_argument("--source-uri", required=True)
    observation.add_argument("--content-file", required=True)
    observation.add_argument("--publisher", help="Required for web evidence")
    observation.add_argument(
        "--applicability",
        help="Required for web evidence; product, cloud, version, and decision scope",
    )
    observation.set_defaults(handler=command_register_observation)

    status = subparsers.add_parser("status", help="Show resumable state and changed sources")
    _add_project_args(status)
    status.set_defaults(handler=command_status)

    authorize_parser = subparsers.add_parser(
        "authorize-action", help="Evaluate a Databricks action against boundary and policy"
    )
    _add_project_args(authorize_parser)
    authorize_parser.add_argument("--action", required=True)
    authorize_parser.add_argument("--resource-name", required=True)
    authorize_parser.add_argument("--system")
    authorize_parser.add_argument("--catalog")
    authorize_parser.add_argument("--schema")
    authorize_parser.set_defaults(handler=command_authorize)

    resource = subparsers.add_parser("record-resource", help="Record an agent-created resource")
    _add_project_args(resource)
    resource.add_argument("--type", required=True)
    resource.add_argument("--name", required=True)
    resource.add_argument("--uri")
    resource.add_argument("--purpose", required=True)
    resource.set_defaults(handler=command_record_resource)

    review = subparsers.add_parser(
        "review-source",
        help="Resolve a pending source revision after impact review",
    )
    _add_project_args(review)
    review.add_argument("--revision-id", required=True)
    review.add_argument(
        "--disposition",
        choices=("applied", "reviewed-no-change", "out-of-scope"),
        required=True,
    )
    review.add_argument("--concept", action="append", help="Affected canonical ID; repeatable")
    review.add_argument("--reason", required=True)
    review.set_defaults(handler=command_review_source)

    question = subparsers.add_parser("record-question", help="Persist a blocking or non-blocking question")
    _add_project_args(question)
    question.add_argument("--id", required=True)
    question.add_argument("--question", required=True)
    question.add_argument("--owner")
    question.add_argument("--blocking", action=argparse.BooleanOptionalAction, default=True)
    question.set_defaults(handler=command_record_question)

    resolve = subparsers.add_parser("resolve-question", help="Resolve a persisted question")
    _add_project_args(resolve)
    resolve.add_argument("--id", required=True)
    resolve.add_argument("--resolution", required=True)
    resolve.set_defaults(handler=command_resolve_question)

    index = subparsers.add_parser("rebuild-index", help="Regenerate OKF navigation")
    _add_project_args(index)
    index.set_defaults(handler=command_rebuild_index)

    validate = subparsers.add_parser("validate", help="Validate OKF and DE Agents profile rules")
    _add_project_args(validate)
    validate.add_argument("--profile", action="store_true")
    validate.set_defaults(handler=command_validate)

    phase = subparsers.add_parser("set-phase", help="Update the resumable discovery phase")
    _add_project_args(phase)
    phase.add_argument(
        "--phase",
        required=True,
        choices=("intake", "clarify", "plan", "discover", "synthesize", "validate", "complete", "blocked"),
    )
    phase.add_argument("--last-step")
    phase.set_defaults(handler=command_set_phase)

    score = subparsers.add_parser("score-candidates", help="Validate and rank candidate assets")
    score.add_argument("--input", required=True, help="YAML or JSON candidate file")
    score.set_defaults(handler=command_score_candidates)

    export = subparsers.add_parser(
        "export-ingestion-config",
        help="Export one implementation-ready OKF ingestion spec as plain YAML",
    )
    _add_project_args(export)
    export.add_argument("--canonical-id", required=True)
    export.add_argument(
        "--output",
        help="Project-relative output path; defaults to .de-discovery/reports/ingestion-configs/",
    )
    export.set_defaults(handler=command_export_ingestion_config)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    handler: Callable[[argparse.Namespace], int] = args.handler
    try:
        return handler(args)
    except DiscoveryError as exc:
        _print({"error": str(exc), "type": "DiscoveryError"})
        return 1
    except KeyboardInterrupt:
        _print({"error": "Interrupted", "type": "KeyboardInterrupt"})
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
