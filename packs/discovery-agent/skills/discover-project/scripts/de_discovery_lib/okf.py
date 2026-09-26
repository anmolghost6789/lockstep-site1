"""OKF v0.2 parsing, profile validation, and deterministic index generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import yaml

from . import __version__
from .config import required_facets
from .contracts import COMPLETENESS_STATUSES, validate_specialized_concept
from .ingestion import READY_STATUSES
from .io import RuntimePaths, atomic_write_json, atomic_write_text, utc_now
from .security import scan_text
from .state import all_source_revision_ids


ALLOWED_STATUS = {"draft", "stable", "deprecated"}
ALLOWED_OBSERVATION = {"observed", "reported", "inferred", "proposed"}
REQUIRED_ROLES = {"context_manifest", "discovery_boundary", "readiness_assessment"}
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
FOOTNOTE_RE = re.compile(r"\[\^([A-Za-z0-9_.:-]+)\]")
FOOTNOTE_DEFINITION_RE = re.compile(r"^\[\^([A-Za-z0-9_.:-]+)\]:", re.MULTILINE)


@dataclass(frozen=True)
class Concept:
    path: Path
    relative_path: Path
    metadata: dict[str, Any]
    body: str

    @property
    def concept_id(self) -> str:
        return self.relative_path.with_suffix("").as_posix()

    @property
    def title(self) -> str:
        value = self.metadata.get("title")
        return value.strip() if isinstance(value, str) and value.strip() else self.concept_id

    @property
    def role(self) -> str | None:
        extension = self.metadata.get("de_agents")
        if isinstance(extension, dict) and isinstance(extension.get("role"), str):
            return extension["role"]
        return None


def _parse_markdown(path: Path, root: Path) -> Concept:
    relative = path.relative_to(root)
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        raise ValueError("missing YAML frontmatter")
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return Concept(path=path, relative_path=relative, metadata=metadata, body=content[match.end() :])


def load_concepts(root: Path) -> tuple[list[Concept], list[dict[str, str]]]:
    concepts: list[Concept] = []
    errors: list[dict[str, str]] = []
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if relative.as_posix() in {"index.md", "log.md"}:
            continue
        try:
            concepts.append(_parse_markdown(path, root))
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append({"path": relative.as_posix(), "message": str(exc)})
    return concepts, errors


def _parse_timestamp(value: Any) -> bool:
    if isinstance(value, datetime):
        return True
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _resolve_link(concept: Concept, target: str, root: Path) -> Path | None:
    clean = unquote(target.split("#", 1)[0].strip())
    if not clean or clean.startswith(("http://", "https://", "mailto:", "evidence:", "file+sha256:")):
        return None
    if clean.startswith("/"):
        candidate = root / clean.lstrip("/")
    else:
        candidate = concept.path.parent / clean
    return candidate.resolve()


def _linked_paths(concept: Concept, root: Path) -> set[Path]:
    return {
        resolved
        for target in LINK_RE.findall(concept.body)
        if (resolved := _resolve_link(concept, target, root)) is not None
    }


def _validate_log(
    path: Path,
    errors: list[dict[str, str]],
    *,
    require_entry: bool,
) -> None:
    if not path.exists():
        errors.append({"path": "log.md", "message": "required root log.md is missing"})
        return
    headings = re.findall(r"^## (\d{4}-\d{2}-\d{2})\s*$", path.read_text(encoding="utf-8"), re.MULTILINE)
    dates: list[date] = []
    for heading in headings:
        try:
            dates.append(date.fromisoformat(heading))
        except ValueError:
            errors.append({"path": "log.md", "message": f"invalid date heading: {heading}"})
    if dates != sorted(dates, reverse=True):
        errors.append({"path": "log.md", "message": "date headings must be newest first"})
    if require_entry and not dates:
        errors.append({"path": "log.md", "message": "profile requires at least one dated change entry"})


def _validate_index(path: Path, errors: list[dict[str, str]]) -> None:
    if not path.exists():
        errors.append({"path": "index.md", "message": "required root index.md is missing"})
        return
    try:
        concept = _parse_markdown(path, path.parent)
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append({"path": "index.md", "message": str(exc)})
        return
    if concept.metadata != {"okf_version": "0.2"}:
        errors.append(
            {
                "path": "index.md",
                "message": 'root frontmatter must contain only okf_version: "0.2"',
            }
        )


def _evidence_exists(resource: str, paths: RuntimePaths) -> bool:
    prefix = "evidence://sha256/"
    if not resource.startswith(prefix):
        return True
    remainder = resource[len(prefix) :]
    parts = remainder.split("/", 1)
    if len(parts) != 2 or not re.fullmatch(r"[a-f0-9]{64}", parts[0]):
        return False
    candidate = paths.evidence_root / "sha256" / parts[0] / parts[1]
    try:
        candidate.resolve().relative_to(paths.evidence_root.resolve())
    except ValueError:
        return False
    return candidate.is_file()


def validate_bundle(
    paths: RuntimePaths,
    config: dict[str, Any],
    state: dict[str, Any],
    *,
    profile: bool,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    _validate_index(paths.knowledge_root / "index.md", errors)
    _validate_log(paths.knowledge_root / "log.md", errors, require_entry=profile)
    for root_name in ("index.md", "log.md"):
        root_path = paths.knowledge_root / root_name
        if root_path.exists():
            for finding in scan_text(root_path.read_text(encoding="utf-8")):
                errors.append(
                    {
                        "path": root_name,
                        "message": f"potential secret at line {finding.line} ({finding.detector})",
                    }
                )

    concepts, parse_errors = load_concepts(paths.knowledge_root)
    errors.extend(parse_errors)
    canonical: dict[str, str] = {}
    roles: dict[str, list[Concept]] = {}
    known_revisions = all_source_revision_ids(state)

    for concept in concepts:
        rel = concept.relative_path.as_posix()
        metadata = concept.metadata
        concept_type = metadata.get("type")
        if not isinstance(concept_type, str) or not concept_type.strip():
            errors.append({"path": rel, "message": "type must be a non-empty string"})

        status = metadata.get("status")
        if status is not None and status not in ALLOWED_STATUS:
            errors.append({"path": rel, "message": f"invalid status {status!r}"})
        stale_after = metadata.get("stale_after")
        if stale_after is not None:
            try:
                date.fromisoformat(str(stale_after))
            except ValueError:
                errors.append({"path": rel, "message": "stale_after must be an ISO-8601 date"})

        generated = metadata.get("generated")
        if generated is not None:
            if not isinstance(generated, dict):
                errors.append({"path": rel, "message": "generated must be a mapping"})
            elif not isinstance(generated.get("by"), str) or not _parse_timestamp(generated.get("at")):
                errors.append({"path": rel, "message": "generated requires string by and ISO-8601 at"})
        else:
            warnings.append({"path": rel, "message": "generated provenance is recommended"})

        verified = metadata.get("verified")
        verified_items = verified if isinstance(verified, list) else [verified] if verified else []
        for item in verified_items:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("by"), str)
                or not _parse_timestamp(item.get("at"))
            ):
                errors.append({"path": rel, "message": "verified entries require by and ISO-8601 at"})

        source_ids: set[str] = set()
        sources = metadata.get("sources", [])
        if sources is not None and not isinstance(sources, list):
            errors.append({"path": rel, "message": "sources must be a list"})
            sources = []
        for source in sources or []:
            if not isinstance(source, dict) or not isinstance(source.get("resource"), str):
                errors.append({"path": rel, "message": "every source requires a resource string"})
                continue
            source_id = source.get("id")
            if source_id is not None:
                if not isinstance(source_id, str) or not source_id:
                    errors.append({"path": rel, "message": "source id must be a non-empty string"})
                elif source_id in source_ids:
                    errors.append({"path": rel, "message": f"duplicate source id {source_id!r}"})
                else:
                    source_ids.add(source_id)
            if not _evidence_exists(source["resource"], paths):
                errors.append(
                    {"path": rel, "message": f"evidence resource is invalid or missing: {source['resource']}"}
                )

        citations: set[str] = set()
        for line in concept.body.splitlines():
            if FOOTNOTE_DEFINITION_RE.match(line):
                continue
            citations.update(FOOTNOTE_RE.findall(line))
        for citation in sorted(citations):
            if citation not in source_ids:
                errors.append(
                    {"path": rel, "message": f"claim citation {citation!r} has no matching sources[].id"}
                )

        extension = metadata.get("de_agents")
        if extension is not None and not isinstance(extension, dict):
            errors.append({"path": rel, "message": "de_agents must be a mapping"})
            extension = {}
        if isinstance(extension, dict):
            identity = extension.get("canonical_id")
            if identity is not None:
                if not isinstance(identity, str) or not identity.strip():
                    errors.append({"path": rel, "message": "de_agents.canonical_id must be non-empty"})
                elif identity in canonical:
                    errors.append(
                        {
                            "path": rel,
                            "message": f"canonical_id {identity!r} also used by {canonical[identity]}",
                        }
                    )
                else:
                    canonical[identity] = rel

            observation = extension.get("observation")
            if observation is not None and observation not in ALLOWED_OBSERVATION:
                errors.append({"path": rel, "message": f"invalid observation {observation!r}"})

            role = extension.get("role")
            if role is not None:
                if not isinstance(role, str) or not role.strip():
                    errors.append({"path": rel, "message": "de_agents.role must be non-empty"})
                else:
                    roles.setdefault(role, []).append(concept)

            revision_ids = extension.get("source_revision_ids", [])
            if not isinstance(revision_ids, list) or any(
                not isinstance(item, str) for item in revision_ids
            ):
                errors.append({"path": rel, "message": "source_revision_ids must be strings"})
            else:
                for revision_id in revision_ids:
                    if revision_id not in known_revisions:
                        errors.append(
                            {
                                "path": rel,
                                "message": f"unknown source revision id {revision_id!r}",
                            }
                        )

        validate_specialized_concept(
            metadata,
            role=concept.role,
            path=rel,
            errors=errors,
        )

        for resolved in _linked_paths(concept, paths.knowledge_root):
            try:
                resolved.relative_to(paths.knowledge_root.resolve())
            except ValueError:
                errors.append({"path": rel, "message": f"link escapes knowledge root: {resolved}"})
                continue
            if not resolved.exists():
                errors.append({"path": rel, "message": f"broken local link: {resolved}"})

        for finding in scan_text(concept.path.read_text(encoding="utf-8")):
            errors.append(
                {
                    "path": rel,
                    "message": f"potential secret at line {finding.line} ({finding.detector})",
                }
            )

    active_acquisition_contracts = {
        item.metadata.get("de_agents", {}).get("canonical_id"): item
        for item in roles.get("acquisition_contract", [])
        if item.metadata.get("status") != "deprecated"
        and item.metadata.get("de_agents", {}).get("canonical_id")
    }
    for concept in roles.get("ingestion_spec", []):
        if concept.metadata.get("status") == "deprecated":
            continue
        extension = concept.metadata.get("de_agents", {})
        spec_status = extension.get("spec_status")
        for derived_id in extension.get("derived_from", []):
            contract = active_acquisition_contracts.get(derived_id)
            if contract is None:
                errors.append(
                    {
                        "path": concept.relative_path.as_posix(),
                        "message": (
                            "ingestion spec de_agents.derived_from must reference an active "
                            f"acquisition_contract canonical ID; unknown {derived_id!r}"
                        ),
                    }
                )
                continue
            contract_status = contract.metadata.get("de_agents", {}).get("contract_status")
            if spec_status in READY_STATUSES and contract_status == "assessed":
                errors.append(
                    {
                        "path": concept.relative_path.as_posix(),
                        "message": (
                            f"{spec_status} ingestion spec requires a feasible or later "
                            f"acquisition contract; {derived_id!r} is only assessed"
                        ),
                    }
                )
            if spec_status in {"approved", "deployed"} and contract_status not in {
                "approved",
                "implementation-ready",
                "deployed",
            }:
                errors.append(
                    {
                        "path": concept.relative_path.as_posix(),
                        "message": (
                            f"{spec_status} ingestion spec requires an approved or later "
                            f"acquisition contract; {derived_id!r} is {contract_status!r}"
                        ),
                    }
                )

    if profile:
        configured_facets = required_facets(config)
        configured_archetypes = set(config["engagement"]["archetypes"])
        active_roles = {
            role: [item for item in items if item.metadata.get("status") != "deprecated"]
            for role, items in roles.items()
        }
        for role in sorted(REQUIRED_ROLES):
            count = len(active_roles.get(role, []))
            if count != 1:
                errors.append(
                    {
                        "path": ".",
                        "message": f"profile requires exactly one active {role!r} concept; found {count}",
                    }
                )
        manifests = active_roles.get("context_manifest", [])
        if len(manifests) == 1:
            manifest_extension = manifests[0].metadata.get("de_agents", {})
            if manifest_extension.get("readiness_target") != config["readiness_target"]:
                errors.append(
                    {
                        "path": manifests[0].relative_path.as_posix(),
                        "message": "context manifest readiness_target must match project config",
                    }
                )
            declared_archetypes = manifest_extension.get("engagement_archetypes")
            if (
                not isinstance(declared_archetypes, list)
                or any(not isinstance(item, str) for item in declared_archetypes)
                or set(declared_archetypes) != configured_archetypes
            ):
                errors.append(
                    {
                        "path": manifests[0].relative_path.as_posix(),
                        "message": "context manifest engagement_archetypes must match project config",
                    }
                )
            declared_facets = manifest_extension.get("required_facets")
            if (
                not isinstance(declared_facets, list)
                or any(not isinstance(item, str) for item in declared_facets)
                or set(declared_facets) != configured_facets
            ):
                errors.append(
                    {
                        "path": manifests[0].relative_path.as_posix(),
                        "message": "context manifest required_facets must match resolved project facets",
                    }
                )
            facet_coverage = manifest_extension.get("facet_coverage")
            if not isinstance(facet_coverage, dict):
                errors.append(
                    {
                        "path": manifests[0].relative_path.as_posix(),
                        "message": "context manifest facet_coverage must be a mapping",
                    }
                )
            else:
                for facet in sorted(configured_facets):
                    if facet_coverage.get(facet) not in COMPLETENESS_STATUSES:
                        errors.append(
                            {
                                "path": manifests[0].relative_path.as_posix(),
                                "message": (
                                    f"facet_coverage.{facet} must be one of "
                                    f"{sorted(COMPLETENESS_STATUSES)}"
                                ),
                            }
                        )
            downstream_context = manifest_extension.get("downstream_context")
            if not isinstance(downstream_context, dict):
                errors.append(
                    {
                        "path": manifests[0].relative_path.as_posix(),
                        "message": "context manifest downstream_context must be a mapping",
                    }
                )
            else:
                for downstream_agent in ("requirements", "design", "build"):
                    routed_ids = downstream_context.get(downstream_agent)
                    if not isinstance(routed_ids, list) or any(
                        not isinstance(item, str) for item in routed_ids
                    ):
                        errors.append(
                            {
                                "path": manifests[0].relative_path.as_posix(),
                                "message": (
                                    f"downstream_context.{downstream_agent} "
                                    "must be a list of canonical IDs"
                                ),
                            }
                        )
                        continue
                    for canonical_id in routed_ids:
                        if canonical_id not in canonical:
                            errors.append(
                                {
                                    "path": manifests[0].relative_path.as_posix(),
                                    "message": (
                                        f"downstream_context.{downstream_agent} references "
                                        f"unknown canonical_id {canonical_id!r}"
                                    ),
                                }
                            )
            expected_resources = {
                f"{item.get('type')}:{item.get('name')}"
                for item in state.get("created_resources", [])
            }
            declared_resources = manifest_extension.get("created_resource_ids", [])
            if not isinstance(declared_resources, list) or any(
                not isinstance(item, str) for item in declared_resources
            ):
                errors.append(
                    {
                        "path": manifests[0].relative_path.as_posix(),
                        "message": "created_resource_ids must be a list of strings",
                    }
                )
            elif not expected_resources.issubset(set(declared_resources)):
                errors.append(
                    {
                        "path": manifests[0].relative_path.as_posix(),
                        "message": "context manifest does not declare every recorded created resource",
                    }
                )
            linked = _linked_paths(manifests[0], paths.knowledge_root)
            for required in ("discovery_boundary", "readiness_assessment"):
                targets = {item.path.resolve() for item in active_roles.get(required, [])}
                if targets and not linked.intersection(targets):
                    errors.append(
                        {
                            "path": manifests[0].relative_path.as_posix(),
                            "message": f"context manifest must link to the active {required}",
                        }
                    )
            specialized_roles: set[str] = set()
            if "acquisition" in configured_facets:
                specialized_roles.update(
                    {"source_system_profile", "acquisition_contract", "ingestion_spec"}
                )
            if "migration-modernization" in configured_archetypes:
                specialized_roles.update({"migration_assessment", "migration_unit"})
                if config["readiness_target"] == "design-ready":
                    specialized_roles.add("migration_plan")
            for required in sorted(specialized_roles):
                targets = {
                    item.path.resolve()
                    for item in active_roles.get(required, [])
                }
                if not targets:
                    errors.append(
                        {
                            "path": ".",
                            "message": f"project profile requires at least one active {required!r} concept",
                        }
                    )
                elif not targets.issubset(linked):
                    errors.append(
                        {
                            "path": manifests[0].relative_path.as_posix(),
                            "message": f"context manifest must link to every active {required}",
                        }
                    )
            ingestion_ids = {
                item.metadata.get("de_agents", {}).get("canonical_id")
                for item in active_roles.get("ingestion_spec", [])
            }
            ingestion_ids.discard(None)
            if ingestion_ids and isinstance(downstream_context, dict):
                for downstream_agent in ("design", "build"):
                    routed_ids = downstream_context.get(downstream_agent)
                    if isinstance(routed_ids, list):
                        missing_ids = sorted(ingestion_ids - set(routed_ids))
                        if missing_ids:
                            errors.append(
                                {
                                    "path": manifests[0].relative_path.as_posix(),
                                    "message": (
                                        f"downstream_context.{downstream_agent} must route "
                                        f"every active ingestion_spec: {missing_ids}"
                                    ),
                                }
                            )
            if (
                "acquisition" in configured_facets
                and config["readiness_target"] == "design-ready"
            ):
                for item in active_roles.get("ingestion_spec", []):
                    spec_status = item.metadata.get("de_agents", {}).get("spec_status")
                    if spec_status not in READY_STATUSES:
                        errors.append(
                            {
                                "path": item.relative_path.as_posix(),
                                "message": (
                                    "design-ready acquisition requires every active "
                                    "ingestion_spec to be implementation-ready or later"
                                ),
                            }
                        )
            open_questions = [
                item for item in state.get("open_questions", []) if item.get("status") == "open"
            ]
            if open_questions:
                question_concepts = {
                    item.path.resolve()
                    for item in active_roles.get("open_questions", [])
                }
                if len(question_concepts) != 1:
                    errors.append(
                        {
                            "path": ".",
                            "message": "open state questions require exactly one active open_questions concept",
                        }
                    )
                elif not linked.intersection(question_concepts):
                    errors.append(
                        {
                            "path": manifests[0].relative_path.as_posix(),
                            "message": "context manifest must link to the active open_questions concept",
                        }
                    )

        boundaries = active_roles.get("discovery_boundary", [])
        if len(boundaries) == 1:
            extension = boundaries[0].metadata.get("de_agents", {})
            if extension.get("boundary_status") != "active":
                errors.append(
                    {
                        "path": boundaries[0].relative_path.as_posix(),
                        "message": "active discovery boundary requires de_agents.boundary_status: active",
                    }
                )

        readiness = active_roles.get("readiness_assessment", [])
        readiness_result = None
        if len(readiness) == 1:
            extension = readiness[0].metadata.get("de_agents", {})
            if extension.get("readiness_target") != config["readiness_target"]:
                errors.append(
                    {
                        "path": readiness[0].relative_path.as_posix(),
                        "message": "readiness assessment target must match project config",
                    }
                )
            readiness_result = extension.get("readiness_result")
            if readiness_result not in {"supported", "conditional", "blocked"}:
                errors.append(
                    {
                        "path": readiness[0].relative_path.as_posix(),
                        "message": "readiness_result must be supported, conditional, or blocked",
                    }
                )

        for review in state.get("source_reviews", []):
            if review.get("disposition") == "applied":
                for canonical_id in review.get("concepts", []):
                    if canonical_id not in canonical:
                        errors.append(
                            {
                                "path": ".de-discovery/state.yaml",
                                "message": f"source review references unknown canonical_id {canonical_id!r}",
                            }
                        )

    report = {
        "valid": not errors,
        "profile": profile,
        "validated_at": utc_now(),
        "knowledge_root": str(paths.knowledge_root),
        "concept_count": len(concepts),
        "errors": errors,
        "warnings": warnings,
        "readiness_result": readiness_result if profile else None,
    }
    paths.reports_root.mkdir(parents=True, exist_ok=True)
    atomic_write_json(paths.reports_root / "validation.json", report)
    return report


def impacted_concepts(root: Path, revision_id: str | None) -> list[dict[str, str]]:
    if not revision_id:
        return []
    concepts, _ = load_concepts(root)
    impacted: list[dict[str, str]] = []
    for concept in concepts:
        extension = concept.metadata.get("de_agents")
        source_ids = extension.get("source_revision_ids", []) if isinstance(extension, dict) else []
        sources = concept.metadata.get("sources", [])
        frontmatter_ids = {
            source.get("id")
            for source in sources
            if isinstance(source, dict) and isinstance(source.get("id"), str)
        } if isinstance(sources, list) else set()
        if revision_id in source_ids or revision_id in frontmatter_ids:
            impacted.append(
                {
                    "path": concept.relative_path.as_posix(),
                    "canonical_id": str(
                        extension.get("canonical_id", concept.concept_id)
                        if isinstance(extension, dict)
                        else concept.concept_id
                    ),
                }
            )
    return impacted


def rebuild_index(paths: RuntimePaths) -> dict[str, Any]:
    concepts, errors = load_concepts(paths.knowledge_root)
    if errors:
        return {"rebuilt": False, "errors": errors}

    active_roles: dict[str, Concept] = {}
    for concept in concepts:
        if concept.role and concept.metadata.get("status") != "deprecated":
            active_roles.setdefault(concept.role, concept)

    lines = [
        "---",
        'okf_version: "0.2"',
        "---",
        "",
        "# Knowledge index",
        "",
        "Start with the context manifest, then follow only the concepts needed for the current task.",
        "",
        "## DE Agent entrypoints",
        "",
    ]
    entrypoints = [
        ("Context manifest", active_roles.get("context_manifest")),
        ("Discovery boundary", active_roles.get("discovery_boundary")),
        ("Readiness assessment", active_roles.get("readiness_assessment")),
    ]
    for label, concept in entrypoints:
        if concept:
            lines.append(f"- {label}: [{concept.title}](/{concept.relative_path.as_posix()})")
        else:
            lines.append(f"- {label}: _not created yet_")
    lines.append("- Change history: [Knowledge log](/log.md)")

    lines.extend(["", "## Concepts", ""])
    grouped: dict[str, list[Concept]] = {}
    for concept in concepts:
        group = concept.relative_path.parent.as_posix()
        grouped.setdefault(group if group != "." else "Root", []).append(concept)
    if not grouped:
        lines.append("_No concepts created yet._")
    else:
        for group in sorted(grouped, key=str.casefold):
            lines.extend([f"### {group}", ""])
            for concept in sorted(grouped[group], key=lambda item: item.title.casefold()):
                description = concept.metadata.get("description")
                suffix = f" — {description.strip()}" if isinstance(description, str) and description.strip() else ""
                lines.append(
                    f"- [{concept.title}](/{concept.relative_path.as_posix()}) "
                    f"(`{concept.metadata.get('type', 'unknown')}`){suffix}"
                )
            lines.append("")

    lines.extend(
        [
            "## Bundle metadata",
            "",
            f"- Generated by `de-discovery/{__version__}` at `{utc_now()}`.",
            f"- Concepts: {len(concepts)}.",
            "",
        ]
    )
    atomic_write_text(paths.knowledge_root / "index.md", "\n".join(lines))
    return {"rebuilt": True, "concept_count": len(concepts), "path": str(paths.knowledge_root / "index.md")}
