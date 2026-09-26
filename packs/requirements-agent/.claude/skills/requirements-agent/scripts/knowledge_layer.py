#!/usr/bin/env python3
"""Manage the Requirements Agent's linked Markdown knowledge layer.

The model owns semantic Markdown. This module owns only deterministic state:
input hashes, stable source IDs, link checks, entity fingerprints, deliverable
impact, render-block ownership, and guarded targeted replacements.

No command creates semantic packets, model-authored plans, chunks, or prose.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any

from urllib.parse import unquote

import yaml


SCHEMA_VERSION = "requirements-state-3.0"
STATE_PATH = PurePosixPath("outputs/00_state/state.json")
KNOWLEDGE_PATH = PurePosixPath("outputs/00_state/knowledge")
INPUT_MANIFEST_PATH = PurePosixPath("inputs_manifest.json")
INPUT_REPORT_PATH = PurePosixPath("outputs/01_input_evaluation/input_evaluation.md")
EVALUATION_PATH = PurePosixPath("outputs/03_evaluation")
EVALUATION_PENDING_PATH = EVALUATION_PATH / ".pending"
EVALUATION_FILENAMES = (
    "evaluation_report.md",
    "quality_scores.json",
    "traceability.yaml",
)
INPUT_REPORT_SPINE = (
    "## §1 · Can we deliver?",
    "## §2 · What we evaluated",
    "## §3 · Findings",
    "## §4 · Checks run",
    "## §5 · Assumptions if proceeding",
    "## §6 · What to do next",
)

OKF_VERSION = "0.1"
CONCEPT_REQUIRED_FIELDS = ("type", "title", "description")
KNOWLEDGE_REQUIRED_FIELDS = (
    "canonical_id",
    "status",
    "confidence",
    "outputs",
)
KNOWLEDGE_STATUSES = {
    "assumption",
    "confirmed",
    "conflicted",
    "draft",
    "insufficient",
    "superseded",
}
KNOWLEDGE_CONFIDENCE = {"high", "medium", "low", "unknown"}
COVERAGE_DISPOSITIONS = {
    "captured",
    "context-only",
    "contradiction",
    "duplicate",
    "out-of-scope",
    "superseded",
    "unresolved",
}
RELATION_TYPES = {
    "contradicts",
    "depends_on",
    "has_part",
    "implemented_by",
    "part_of",
    "related_to",
    "satisfies",
    "superseded_by",
    "supersedes",
}
ACYCLIC_RELATION_TYPES = {"depends_on", "part_of"}

ENTITY_HEADING_RE = re.compile(
    r"^(?P<marks>#{1,4})\s+(?P<id>[A-Z][A-Z0-9]{0,11}(?:-[A-Z][A-Z0-9]{0,11})*-\d{1,8})\b(?P<title>.*)$",
    re.MULTILINE,
)
DELIVERABLES_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*|__)?(?:Deliverables|Applies to)(?:\*\*|__)?\s*:\s*(?P<values>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
ENTITY_TYPE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*|__)?Type(?:\*\*|__)?\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
ENTITY_STATUS_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*|__)?Status(?:\*\*|__)?\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
ENTITY_CONFIDENCE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*|__)?Confidence(?:\*\*|__)?\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
STANDALONE_REASON_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*|__)?Standalone reason(?:\*\*|__)?\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\((?P<target>[^)]+)\)")
WIKI_LINK_RE = re.compile(r"\[\[(?P<target>[^\]]+)\]\]")
BLOCK_START_RE = re.compile(
    r'^<!-- RA-BLOCK START id="(?P<id>[A-Za-z0-9_.:-]+)"'
    r'(?: entities="(?P<entities>[^"]*)")?'
    r'(?: sha256="(?P<declared_sha256>[a-f0-9]{64})")? -->\s*$',
    re.MULTILINE,
)
BLOCK_END_TEMPLATE = '<!-- RA-BLOCK END id="{block_id}" -->'
BLOCK_AUTHOR_START_TEMPLATE = (
    '<!-- RA-BLOCK START id="<semantic-block-id>" '
    'entities="<comma-separated canonical IDs>" -->'
)
BLOCK_AUTHOR_END_TEMPLATE = '<!-- RA-BLOCK END id="<same semantic-block-id>" -->'
BLOCK_MARKER_RE = re.compile(r"^<!-- RA-BLOCK (?:START|END).*?-->\s*\n?", re.MULTILINE)
RETRIEVAL_CHECKPOINT_RE = re.compile(
    r'<!-- RA-RETRIEVAL-CHECKPOINT route="(?P<route>[^"]+)" '
    r'(?:entities="(?P<entities>[^"]*)" )?'
    r'sha256="(?P<sha256>[a-f0-9]{64})" -->\s*$',
    re.MULTILINE,
)
RETRIEVAL_RECEIPT_RE = re.compile(
    r'<!-- RA-RETRIEVAL-RECEIPT deliverable="(?P<deliverable>[A-Z0-9_-]+)" '
    r'batch="(?P<batch>[A-Za-z0-9_.:-]+)" '
    r'sha256="(?P<sha256>[a-f0-9]{64})" -->\s*$',
    re.MULTILINE,
)
RELATION_LINE_RE = re.compile(
    r"^\s*[-*]\s*(?P<kind>[a-z][a-z0-9_]*)\s*:\s*(?P<targets>.+?)\s*$",
    re.MULTILINE,
)
ENTITY_ID_RE = re.compile(r"[A-Z][A-Z0-9]{0,11}(?:-[A-Z][A-Z0-9]{0,11})*-\d{1,8}")
RELATIONS_HEADING_RE = re.compile(
    r"^#{2,6}\s+Relations\s*$", re.IGNORECASE | re.MULTILINE
)
SOURCE_HEADING_RE = re.compile(r"^#{1,6}\s+(?P<title>\S.*)$", re.MULTILINE)
REQUIREMENT_SIGNAL_RE = re.compile(
    r"\b(?:shall|must|required|requirement|constraint|acceptance|decision|kpi)\b",
    re.IGNORECASE,
)

# Keep each authoring receipt below the runtime's large-tool-result spill range.
# This is a transport boundary, not a document length or content quota.
AUTHORING_BATCH_CHAR_BUDGET = 24_000
AUTHORING_BATCH_ENTITY_LIMIT = 40
# Tool-call payloads materially above this context size risk a long or truncated
# single Write. This controls transport strategy only; it does not cap content.


class KnowledgeError(RuntimeError):
    """Raised when deterministic knowledge contracts are invalid."""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_retrieval_checkpoint(text: str) -> str:
    return RETRIEVAL_RECEIPT_RE.sub("", RETRIEVAL_CHECKPOINT_RE.sub("", text))


def _frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse one OKF concept without inventing a second metadata format."""
    if not text.startswith("---\n"):
        raise KnowledgeError("missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise KnowledgeError("unterminated YAML frontmatter")
    try:
        value = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        raise KnowledgeError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(value, dict):
        raise KnowledgeError("YAML frontmatter must be a mapping")
    return value, text[end + 5 :]


def _concept_text(metadata: dict[str, Any], body: str) -> str:
    rendered = yaml.safe_dump(
        metadata,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).strip()
    return f"---\n{rendered}\n---\n\n{body.strip()}\n"


def _concept_metadata(path: Path) -> dict[str, Any]:
    metadata, _body = _frontmatter(_read_text(path))
    return metadata


def _relative(run_dir: Path, path: Path) -> str:
    return path.resolve().relative_to(run_dir.resolve()).as_posix()


def _safe_run_path(run_dir: Path, value: str | PurePosixPath) -> Path:
    rel = PurePosixPath(str(value).replace("\\", "/"))
    if rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
        raise KnowledgeError(f"unsafe run-relative path: {value}")
    root = run_dir.resolve()
    path = (root / Path(*rel.parts)).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise KnowledgeError(f"path escapes run directory: {value}") from exc
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _replace_with_retry(temporary, path)


def _replace_with_retry(temporary: Path, target: Path) -> None:
    """Replace a small state file despite transient Windows scanner locks."""
    for attempt in range(5):
        try:
            temporary.replace(target)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05 * (attempt + 1))


def _default_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": None,
        "selected_outputs": [],
        "sources": {},
        "phases": {
            "start": {"status": "pending"},
            "extract": {"status": "pending"},
            "evaluate": {"status": "pending"},
        },
        "extraction": {"status": "pending"},
        "knowledge": {
            "page_hashes": {},
            "entity_hashes": {},
            "entities": {},
            "changed_entities": [],
        },
        "deliverables": {},
        "generation_summary": {},
        "evaluation": {"status": "pending"},
    }


def _load_state(run_dir: Path) -> dict[str, Any]:
    path = _safe_run_path(run_dir, STATE_PATH)
    if not path.is_file():
        return _default_state()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeError(f"invalid state file: {path}") from exc
    if not isinstance(state, dict):
        raise KnowledgeError(f"state must be a JSON object: {path}")
    if state.get("schema_version") != SCHEMA_VERSION:
        raise KnowledgeError(
            f"unsupported state schema {state.get('schema_version')!r}; expected {SCHEMA_VERSION}"
        )
    return state


def _save_state(run_dir: Path, state: dict[str, Any]) -> Path:
    state["updated_at"] = _now()
    path = _safe_run_path(run_dir, STATE_PATH)
    _write_json(path, state)
    return path


def _workflow_manifest() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "workflow_manifest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeError(f"invalid workflow manifest: {path}") from exc
    if not isinstance(payload, dict):
        raise KnowledgeError(f"workflow manifest must be an object: {path}")
    return payload


def _outputs_by_id() -> dict[str, dict[str, Any]]:
    return {
        str(item["id"]).upper(): item
        for item in (_workflow_manifest().get("outputs") or [])
        if isinstance(item, dict) and item.get("id")
    }


def _input_report_template_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "assets"
        / "templates"
        / "reports"
        / "INPUT_EVALUATION_REPORT.template.md"
    )


def _input_report_template_sha256() -> str:
    path = _input_report_template_path()
    if not path.is_file():
        raise KnowledgeError(f"input evaluation template is missing: {path}")
    return _sha_file(path)


def _input_report_spine_errors(report: Path) -> list[str]:
    if not report.is_file() or report.stat().st_size == 0:
        return [f"input evaluation report is missing: {INPUT_REPORT_PATH}"]
    text = _read_text(report)
    errors = [
        f"input evaluation report is missing template section: {heading}"
        for heading in INPUT_REPORT_SPINE
        if heading not in text
    ]
    if not re.search(r"(?m)^> ## (?:✅ PASS|⚠️ WARN|⛔ ERROR)\b", text):
        errors.append("input evaluation report is missing the template verdict banner")
    if "**Readiness**" not in text:
        errors.append("input evaluation report is missing the readiness meter line")
    return errors


def _safe_template_path(run_dir: Path, value: str) -> Path:
    """Resolve a run-local template or an exact manifest-declared default."""
    normalized = PurePosixPath(str(value).replace("\\", "/"))
    declared = {
        str(item.get("template") or "")
        for item in _outputs_by_id().values()
        if item.get("template")
    }
    if normalized.as_posix() in declared:
        # The run's .claude directory is an intentional read-only junction to
        # the canonical skill package. Only exact manifest paths may cross it.
        return (run_dir.resolve() / Path(*normalized.parts)).resolve()
    return _safe_run_path(run_dir, normalized)


def _ensure_layout(run_dir: Path) -> None:
    knowledge = _safe_run_path(run_dir, KNOWLEDGE_PATH)
    (knowledge / "sources").mkdir(parents=True, exist_ok=True)
    index = knowledge / "index.md"
    if not index.exists():
        index.write_text(
            '---\nokf_version: "0.1"\n---\n\n# Requirements Knowledge Index\n',
            encoding="utf-8",
        )
    log = knowledge / "log.md"
    if not log.exists():
        log.write_text("# Requirements Knowledge Update Log\n", encoding="utf-8")


def _slug(value: str) -> str:
    stem = Path(value).stem.lower()
    clean = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return (clean or "source")[:64]


def _source_page(source_id: str, source_path: str) -> str:
    return f"outputs/00_state/knowledge/sources/{source_id}-{_slug(source_path)}.md"


def _write_if_changed(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    _replace_with_retry(temporary, path)


def _relative_link(from_page: Path, target: Path) -> str:
    return os.path.relpath(target, start=from_page.parent).replace("\\", "/")


def _page_title(page: Path) -> str:
    if not page.is_file():
        return page.stem
    try:
        metadata, _body = _frontmatter(_read_text(page))
        if str(metadata.get("title") or "").strip():
            return str(metadata["title"]).strip()
    except KnowledgeError:
        pass
    for line in page.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip() or page.stem
    return page.stem


def _page_description(page: Path) -> str:
    try:
        metadata, _body = _frontmatter(_read_text(page))
    except KnowledgeError:
        return ""
    return str(metadata.get("description") or "").strip()


def _concept_backlinks(run_dir: Path, source_page: Path) -> list[Path]:
    backlinks: list[Path] = []
    for concept in _topic_pages(run_dir):
        for raw_target in _link_targets(_read_text(concept)):
            target = raw_target.strip().strip("<>").partition("#")[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if " " in target:
                target = target.split()[0]
            decoded = unquote(target)
            if not Path(decoded).suffix:
                decoded += ".md"
            if (concept.parent / decoded).resolve() == source_page.resolve():
                backlinks.append(concept)
                break
    return sorted(set(backlinks))


def _preserved_coverage(page: Path) -> list[str]:
    """Keep curator-owned source accounting while refreshing source mechanics."""
    if not page.is_file():
        return [
            "| Locator | Meaning | Concepts | Disposition |",
            "|---|---|---|---|",
            "| Document-wide | Pending semantic extraction | — | unresolved |",
        ]
    try:
        _metadata, body = _frontmatter(_read_text(page))
    except KnowledgeError:
        return []
    match = re.search(
        r"(?ms)^## Coverage\s*\n(?P<body>.*?)(?=^##\s+|\Z)",
        body,
    )
    if not match:
        return []
    return match.group("body").strip().splitlines()


def _render_semantic_indexes(run_dir: Path, knowledge: Path) -> list[str]:
    """Generate progressive-disclosure indexes for input-shaped concept folders."""
    pages = _topic_pages(run_dir)
    semantic_directories: set[Path] = set()
    for page in pages:
        current = page.parent
        while current != knowledge:
            semantic_directories.add(current)
            current = current.parent
    directories = sorted(
        semantic_directories,
        key=lambda path: len(path.parts),
        reverse=True,
    )
    active_directories = {directory.resolve() for directory in directories}
    for stale_index in knowledge.rglob("index.md"):
        if stale_index.parent in {
            knowledge,
            knowledge / "sources",
            knowledge / "coverage",
        }:
            continue
        if stale_index.parent.resolve() not in active_directories:
            stale_index.unlink()
    for directory in directories:
        direct_pages = sorted(page for page in pages if page.parent == directory)
        child_dirs = sorted(
            child
            for child in directory.iterdir()
            if child.is_dir() and any(page.is_relative_to(child) for page in pages)
        )
        lines = [
            f"# {_page_title(directory / 'index.md') if (directory / 'index.md').is_file() else directory.name.replace('-', ' ').title()}",
            "",
        ]
        for child in child_dirs:
            child_index = child / "index.md"
            description = f"{child.name.replace('-', ' ').title()} knowledge concepts."
            lines.append(
                f"- [{child.name.replace('-', ' ').title()}]({_relative_link(directory / 'index.md', child_index)}) - {description}"
            )
        for page in direct_pages:
            lines.append(
                f"- [{_page_title(page)}]({_relative_link(directory / 'index.md', page)})"
                + (f" - {_page_description(page)}" if _page_description(page) else "")
            )
        _write_if_changed(directory / "index.md", "\n".join([*lines, ""]))

    routes: list[str] = []
    top_dirs = sorted(
        {
            page.relative_to(knowledge).parts[0]
            for page in pages
            if len(page.relative_to(knowledge).parts) > 1
        }
    )
    for name in top_dirs:
        directory = knowledge / name
        label = "Topic concepts" if name == "topics" else name.replace("-", " ").title()
        routes.append(
            f"- [{label}]({name}/index.md) - "
            f"Input-shaped route containing {sum(page.is_relative_to(directory) for page in pages)} concepts."
        )
    for page in sorted(page for page in pages if page.parent == knowledge):
        routes.append(
            f"- [{_page_title(page)}]({_relative_link(knowledge / 'index.md', page)})"
            + (f" - {_page_description(page)}" if _page_description(page) else "")
        )
    return routes


def _projected_source_coverage(
    run_dir: Path,
    source_page: Path,
    rows: list[dict[str, Any]],
    entities: dict[str, dict[str, Any]],
) -> list[str]:
    """Render a source-local view from canonical coverage-ledger judgments."""
    lines = [
        "| Locator | Meaning | Concepts | Disposition |",
        "|---|---|---|---|",
    ]
    for row in rows:
        concept_links: list[str] = []
        for entity_id in row.get("concepts") or []:
            entity = entities.get(entity_id)
            if not entity:
                continue
            target = _safe_run_path(run_dir, str(entity["page"]))
            href = _relative_link(source_page, target)
            if entity.get("anchor"):
                href += f"#{entity['anchor']}"
            concept_links.append(f"[{entity_id}]({href})")
        locator = str(row.get("locator") or "").replace("|", r"\|")
        meaning = str(row.get("meaning") or "").replace("|", r"\|")
        concepts = ", ".join(concept_links) or "â€”"
        disposition = str(row.get("disposition") or "unresolved")
        if not concept_links:
            concepts = "none"
        lines.append(f"| {locator} | {meaning} | {concepts} | {disposition} |")
    return lines


def _render_source_nodes_and_index(
    run_dir: Path,
    state: dict[str, Any],
    coverage_rows: dict[str, list[dict[str, Any]]] | None = None,
    entities: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Refresh OKF source concepts and input-shaped progressive-disclosure indexes."""
    _ensure_layout(run_dir)
    knowledge = _safe_run_path(run_dir, KNOWLEDGE_PATH)
    source_entries: list[str] = []
    expected_pages: set[Path] = set()

    records = sorted(
        (
            record
            for record in (state.get("sources") or {}).values()
            if isinstance(record, dict)
            and record.get("semantic")
            and record.get("page")
        ),
        key=lambda record: str(record.get("source_id") or ""),
    )
    for record in records:
        page = _safe_run_path(run_dir, str(record["page"]))
        expected_pages.add(page.resolve())
        source_id = str(record.get("source_id") or "")
        original = str(record.get("path") or "")
        read_path = str(record.get("text_path") or original)
        title = Path(original).stem or source_id
        active = record.get("current_sha256") is not None
        status = "active" if active else "deleted"
        description = f"Provenance pointer for {title}; use during extraction or explicit evidence repair."
        metadata = {
            "type": "Requirements Source",
            "title": f"{source_id} - {title}",
            "description": description,
            "canonical_id": source_id,
            "resource": original,
            "tags": ["source", str(record.get("category") or "uncategorized")],
            "timestamp": str(record.get("knowledge_updated_at") or _now()),
            "status": status,
        }
        lines = [
            f"# {source_id} - {title}",
            "",
            description,
            "",
            f"- Original: `{original}`",
            f"- Category: `{record.get('category') or 'uncategorized'}`",
            f"- Status: `{status}`",
        ]
        read_file = _safe_run_path(run_dir, read_path) if read_path else None
        if active and read_file and read_file.is_file():
            lines.append(
                f"- Resource: [Open original evidence]({_relative_link(page, read_file)})"
            )
        else:
            lines.append("- Resource: unavailable because the source was deleted")
        if record.get("current_sha256"):
            lines.append(f"- Content hash: `{record['current_sha256']}`")
        lines.extend(["", "## Coverage", ""])
        projected = (
            _projected_source_coverage(
                run_dir,
                page,
                (coverage_rows or {}).get(source_id, []),
                entities or {},
            )
            if coverage_rows is not None
            else None
        )
        lines.extend(
            projected
            or _preserved_coverage(page)
            or [
                "| Locator | Meaning | Concepts | Disposition |",
                "|---|---|---|---|",
                "| Document-wide | Pending semantic extraction | — | unresolved |",
            ]
        )
        lines.extend(["", "## Linked concepts", ""])
        backlinks = _concept_backlinks(run_dir, page)
        if backlinks:
            lines.extend(
                f"- [{_page_title(concept)}]({_relative_link(page, concept)})"
                for concept in backlinks
            )
        else:
            lines.append(
                "- None yet. Run `/extract-requirements` to create knowledge concepts."
            )
        _write_if_changed(page, _concept_text(metadata, "\n".join(lines)))
        source_entries.append(
            f"- [{source_id} - {title}]({_relative_link(knowledge / 'sources' / 'index.md', page)}) - {description}"
        )

    sources_dir = knowledge / "sources"
    for stale in sources_dir.glob("*.md"):
        if stale.name == "index.md":
            continue
        if stale.resolve() not in expected_pages:
            stale.unlink()

    _write_if_changed(
        sources_dir / "index.md",
        "\n".join(
            [
                "# Source concepts",
                "",
                "Provenance routes for extraction and explicit evidence repair; generation does not read these pages.",
                "",
                *(source_entries or ["- No semantic sources."]),
                "",
            ]
        ),
    )
    coverage_pages = _coverage_pages(run_dir)
    coverage_dir = knowledge / "coverage"
    if coverage_pages:
        _write_if_changed(
            coverage_dir / "index.md",
            "\n".join(
                [
                    "# Source coverage",
                    "",
                    "Canonical source-to-concept accounting grouped by natural input routes.",
                    "",
                    *[
                        f"- [{_page_title(item)}]({_relative_link(coverage_dir / 'index.md', item)})"
                        + (
                            f" - {_page_description(item)}"
                            if _page_description(item)
                            else ""
                        )
                        for item in coverage_pages
                    ],
                    "",
                ]
            ),
        )
    semantic_routes = _render_semantic_indexes(run_dir, knowledge)
    index_lines = [
        "---",
        f'okf_version: "{OKF_VERSION}"',
        "---",
        "",
        "# Requirements Knowledge Index",
        "",
        "Progressive-disclosure entry point for the local requirements knowledge graph.",
        "",
        "## Knowledge routes",
        "",
        *(
            semantic_routes
            or ["- No semantic concepts yet. Run `/extract-requirements`. "]
        ),
        *(
            [
                "- [Source coverage](coverage/index.md) - Canonical source-to-concept accounting."
            ]
            if coverage_pages
            else []
        ),
        "- [Source concepts](sources/index.md) - Provenance used for extraction and evidence repair.",
        "- [Update log](log.md) - Chronological semantic changes for iterative runs.",
        "",
    ]
    _write_if_changed(knowledge / "index.md", "\n".join(index_lines))


def _is_semantic_source(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    if normalized == "inputs/readme.md" or "/_ingested/" in normalized:
        return False
    if normalized.startswith("inputs/templates/"):
        return False
    if normalized.startswith("context/branding/"):
        return False
    return (
        normalized.startswith("inputs/")
        or normalized.startswith("context/guidance/")
        or normalized.startswith("context/reference/")
    )


def _load_inputs_manifest(run_dir: Path) -> list[dict[str, Any]]:
    path = _safe_run_path(run_dir, INPUT_MANIFEST_PATH)
    if not path.is_file():
        raise KnowledgeError(
            "inputs_manifest.json is missing; run ingest_inputs.py before refreshing knowledge state"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeError(f"invalid inputs manifest: {path}") from exc
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list):
        raise KnowledgeError(f"inputs manifest has no files list: {path}")
    return [item for item in files if isinstance(item, dict) and item.get("path")]


def _next_source_id(sources: dict[str, Any]) -> str:
    numbers = []
    for record in sources.values():
        match = re.fullmatch(r"SRC-(\d+)", str((record or {}).get("source_id") or ""))
        if match:
            numbers.append(int(match.group(1)))
    return f"SRC-{(max(numbers, default=0) + 1):03d}"


def refresh_inputs(run_dir: Path) -> dict[str, Any]:
    """Refresh current input hashes without accepting them as processed."""
    _ensure_layout(run_dir)
    state = _load_state(run_dir)
    sources: dict[str, Any] = state.setdefault("sources", {})
    current_rows = {
        str(row["path"]).replace("\\", "/"): row
        for row in _load_inputs_manifest(run_dir)
        if "/_ingested/" not in str(row["path"]).replace("\\", "/").lower()
        and str(row["path"]).replace("\\", "/").lower() != "inputs/readme.md"
    }

    for source_path, row in current_rows.items():
        record = sources.get(source_path)
        if not isinstance(record, dict):
            source_id = _next_source_id(sources)
            record = {
                "source_id": source_id,
                "path": source_path,
                "page": _source_page(source_id, source_path)
                if _is_semantic_source(source_path)
                else None,
                "committed_sha256": None,
                "extracted_sha256": None,
                "extraction_deletion_committed": False,
            }
            sources[source_path] = record
        previous_current = record.get("current_sha256")
        extraction = (
            row.get("extraction") if isinstance(row.get("extraction"), dict) else {}
        )
        current_sha = str(row.get("sha256") or "")
        record.update(
            {
                "current_sha256": current_sha,
                "text_path": str(extraction.get("text_path") or source_path).replace(
                    "\\", "/"
                ),
                "category": str(row.get("category") or ""),
                "semantic": _is_semantic_source(source_path),
                "deleted": False,
                "deletion_committed": False,
            }
        )
        if previous_current != current_sha or not record.get("knowledge_updated_at"):
            record["knowledge_updated_at"] = _now()

    for source_path, record in sources.items():
        if source_path not in current_rows:
            if record.get("current_sha256") is not None:
                record["knowledge_updated_at"] = _now()
            record["current_sha256"] = None
            record["deleted"] = True

    changes: list[dict[str, Any]] = []
    for source_path, record in sorted(sources.items()):
        committed = record.get("committed_sha256")
        current = record.get("current_sha256")
        if current is None:
            status = "unchanged" if record.get("deletion_committed") else "deleted"
        elif committed is None:
            status = "added"
        elif committed != current:
            status = "modified"
        else:
            status = "unchanged"
        record["status"] = status
        if status != "unchanged":
            changes.append(
                {
                    "source_id": record["source_id"],
                    "status": status,
                    "path": source_path,
                    "text_path": record.get("text_path"),
                    "page": record.get("page"),
                    "semantic": bool(record.get("semantic")),
                }
            )

    _render_source_nodes_and_index(run_dir, state)
    report = _safe_run_path(run_dir, INPUT_REPORT_PATH)
    template_sha256 = _input_report_template_sha256()
    report_refresh_required = state.get(
        "input_report_template_sha256"
    ) != template_sha256 or bool(_input_report_spine_errors(report))
    _save_state(run_dir, state)
    return {
        "state_path": STATE_PATH.as_posix(),
        "knowledge_index": f"{KNOWLEDGE_PATH.as_posix()}/index.md",
        "input_report": INPUT_REPORT_PATH.as_posix(),
        "selected_outputs": list(state.get("selected_outputs") or []),
        "report_refresh_required": report_refresh_required,
        "changes": changes,
        "counts": {
            status: sum(1 for change in changes if change["status"] == status)
            for status in ("added", "modified", "deleted")
        },
    }


def source_overview(
    run_dir: Path,
    phase: str,
    include_unchanged: bool = False,
) -> dict[str, Any]:
    """Return lightweight source routing without persisting another inventory.

    The outline is intentionally structural: it helps a curator choose bounded
    reads but does not try to summarize or semantically extract source prose.
    """
    if phase not in {"start", "extract"}:
        raise KnowledgeError("source overview phase must be start or extract")
    state = _load_state(run_dir)
    rows: list[dict[str, Any]] = []
    total_characters = 0
    for record in sorted(
        (state.get("sources") or {}).values(),
        key=lambda item: str((item or {}).get("source_id") or ""),
    ):
        if not isinstance(record, dict) or not record.get("semantic"):
            continue
        current = record.get("current_sha256")
        if phase == "start":
            status = str(record.get("status") or "unchanged")
        else:
            extracted = record.get("extracted_sha256")
            if current is None:
                status = (
                    "unchanged"
                    if record.get("extraction_deletion_committed")
                    else "deleted"
                )
            elif extracted is None:
                status = "added"
            elif extracted != current:
                status = "modified"
            else:
                status = "unchanged"
        if not include_unchanged and status == "unchanged":
            continue

        read_path = str(record.get("text_path") or record.get("path") or "")
        headings: list[str] = []
        character_count = 0
        line_count = 0
        requirement_signal_count = 0
        if current is not None and read_path:
            source = _safe_run_path(run_dir, read_path)
            if source.is_file():
                text = _read_text(source)
                character_count = len(text)
                line_count = text.count("\n") + (1 if text else 0)
                requirement_signal_count = len(REQUIREMENT_SIGNAL_RE.findall(text))
                headings = [
                    match.group("title").strip()
                    for match in SOURCE_HEADING_RE.finditer(text)
                ]
        total_characters += character_count
        rows.append(
            {
                "source_id": record.get("source_id"),
                "status": status,
                "category": record.get("category"),
                "path": record.get("path"),
                "read_path": read_path,
                "source_page": record.get("page"),
                "character_count": character_count,
                "line_count": line_count,
                "requirement_signal_count": requirement_signal_count,
                "headings": headings,
            }
        )
    return {
        "phase": phase,
        "sources": rows,
        "source_count": len(rows),
        "total_characters": total_characters,
    }


def _all_knowledge_pages(run_dir: Path) -> list[Path]:
    knowledge = _safe_run_path(run_dir, KNOWLEDGE_PATH)
    if not knowledge.is_dir():
        return []
    return sorted(path for path in knowledge.rglob("*.md") if path.is_file())


def _topic_pages(run_dir: Path) -> list[Path]:
    """Return canonical semantic pages across the input-shaped directory taxonomy."""
    knowledge = _safe_run_path(run_dir, KNOWLEDGE_PATH)
    if not knowledge.is_dir():
        return []
    excluded = {(knowledge / "log.md").resolve()}
    pages = []
    for path in knowledge.rglob("*.md"):
        if not path.is_file() or path.name == "index.md" or path.resolve() in excluded:
            continue
        try:
            path.relative_to(knowledge / "sources")
            continue
        except ValueError:
            pass
        try:
            path.relative_to(knowledge / "coverage")
            continue
        except ValueError:
            pass
        pages.append(path)
    return sorted(pages)


def _coverage_pages(run_dir: Path) -> list[Path]:
    """Return canonical, model-authored source-accounting pages.

    Coverage pages are knowledge artifacts, but not requirement entities. They
    are kept separate from ``_topic_pages`` so their source rows cannot be
    mistaken for requirements during impact calculation.
    """
    directory = _safe_run_path(run_dir, KNOWLEDGE_PATH) / "coverage"
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.rglob("*.md")
        if path.is_file() and path.name != "index.md"
    )


def _parse_deliverables(section: str, valid: set[str]) -> list[str]:
    match = DELIVERABLES_RE.search(section)
    if not match:
        return []
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]*", match.group("values"))
    result: list[str] = []
    for token in tokens:
        value = token.upper()
        if value in valid and value not in result:
            result.append(value)
    return result


def _parse_labeled_value(pattern: re.Pattern[str], section: str) -> str:
    match = pattern.search(section)
    return match.group("value").strip() if match else ""


def _has_source_evidence(section: str, page: Path, run_dir: Path) -> bool:
    """Return true when a section links to a page in knowledge/sources.

    Authors normally use a relative link such as ``../sources/SRC-001.md``;
    checking the raw link text for ``knowledge/sources`` rejects that valid
    representation. Resolve local links instead so the evidence contract is
    independent of how deeply the topic page is nested.
    """
    sources_dir = (_safe_run_path(run_dir, KNOWLEDGE_PATH) / "sources").resolve()
    for raw_target in _link_targets(section):
        target = raw_target.strip().strip("<>")
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        file_part = target.partition("#")[0]
        if " " in file_part:
            file_part = file_part.split()[0]
        decoded = unquote(file_part)
        if not Path(decoded).suffix:
            decoded += ".md"
        resolved = (page.parent / decoded).resolve()
        try:
            resolved.relative_to(sources_dir)
        except ValueError:
            continue
        if resolved.is_file():
            return True
    return False


def _source_evidence_records(
    section: str,
    page: Path,
    run_dir: Path,
) -> tuple[list[dict[str, str]], list[str]]:
    """Resolve evidence labels to their canonical source concept identities."""
    records: list[dict[str, str]] = []
    errors: list[str] = []
    for match in re.finditer(r"\[(SRC-\d+)\]\(([^)]+)\)", section):
        source_id, raw_target = match.groups()
        file_part = raw_target.strip().strip("<>").partition("#")[0]
        if " " in file_part:
            file_part = file_part.split()[0]
        decoded = unquote(file_part)
        if not Path(decoded).suffix:
            decoded += ".md"
        target = (page.parent / decoded).resolve()
        if not target.is_file():
            continue
        try:
            metadata, _body = _frontmatter(_read_text(target))
        except KnowledgeError as exc:
            errors.append(
                f"evidence {source_id} points to invalid source concept: {exc}"
            )
            continue
        target_id = str(metadata.get("canonical_id") or "").strip()
        if target_id != source_id:
            errors.append(
                f"evidence label {source_id} points to {target_id or target.name}"
            )
        line_start = section.rfind("\n", 0, match.start()) + 1
        line_end = section.find("\n", match.end())
        line = section[line_start : line_end if line_end >= 0 else len(section)]
        after = line[match.end() - line_start :].strip(" -—–:;\t")
        if not after:
            errors.append(f"evidence {source_id} needs a source locator after its link")
        records.append(
            {
                "source_id": source_id,
                "target": _relative(run_dir, target),
                "locator": after,
            }
        )
    return records, errors


def _markdown_table_cells(line: str) -> list[str]:
    """Split one Markdown table row while preserving escaped literal pipes."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    return [
        cell.strip().replace(r"\|", "|")
        for cell in re.split(r"(?<!\\)\|", stripped.strip("|"))
    ]


def _coverage_ledger_rows(
    run_dir: Path,
    pages: list[Path] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Parse graph-native source accounting from a small set of Markdown pages."""
    rows_by_source: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    sources_dir = (_safe_run_path(run_dir, KNOWLEDGE_PATH) / "sources").resolve()
    state = _load_state(run_dir)
    active_categories = {
        str(record.get("source_id") or ""): str(
            record.get("category") or "uncategorized"
        )
        for record in (state.get("sources") or {}).values()
        if isinstance(record, dict)
        and record.get("semantic")
        and record.get("current_sha256") is not None
    }
    for page in pages if pages is not None else _coverage_pages(run_dir):
        rel = _relative(run_dir, page)
        try:
            metadata, body = _frontmatter(_read_text(page))
        except KnowledgeError as exc:
            errors.append(f"{rel}: {exc}")
            continue
        if str(metadata.get("type") or "").strip() != "Source Coverage Collection":
            errors.append(f"{rel} must have type: Source Coverage Collection")
        match = re.search(
            r"(?ms)^## Source accounting\s*\n(?P<body>.*?)(?=^##\s+|\Z)",
            body,
        )
        if not match:
            errors.append(f"{rel} needs a ## Source accounting table")
            continue
        page_source_ids: set[str] = set()
        for line in match.group("body").splitlines():
            cells = _markdown_table_cells(line)
            if not cells:
                continue
            if len(cells) != 5:
                if set("".join(cells)) <= {"-", ":", " "}:
                    continue
                errors.append(
                    f"{rel} has a source accounting row with {len(cells)} columns; expected 5"
                )
                continue
            if cells[0].lower() == "source" or set(cells[0]) <= {"-", ":"}:
                continue
            source_match = re.fullmatch(r"\[(SRC-\d+)\]\(([^)]+)\)", cells[0].strip())
            if not source_match:
                errors.append(
                    f"{rel} source cell must be a linked SRC-* identity: {cells[0]}"
                )
                continue
            source_id, raw_source_target = source_match.groups()
            page_source_ids.add(source_id)
            decoded_source = unquote(
                raw_source_target.partition("#")[0].strip().strip("<>")
            )
            if not Path(decoded_source).suffix:
                decoded_source += ".md"
            source_target = (page.parent / decoded_source).resolve()
            if not source_target.is_file() or not source_target.is_relative_to(
                sources_dir
            ):
                errors.append(f"{rel} {source_id} points outside the source concepts")
                continue
            try:
                source_metadata, _source_body = _frontmatter(_read_text(source_target))
            except KnowledgeError as exc:
                errors.append(
                    f"{rel} {source_id} points to an invalid source concept: {exc}"
                )
                continue
            if str(source_metadata.get("canonical_id") or "") != source_id:
                errors.append(
                    f"{rel} source label {source_id} points to the wrong source page"
                )
            concept_links = [
                {"label": link.group("label"), "target": link.group("target")}
                for link in re.finditer(
                    r"\[(?P<label>[A-Z][A-Z0-9-]*-\d{1,8})\]\((?P<target>[^)]+)\)",
                    cells[3],
                )
            ]
            rows_by_source.setdefault(source_id, []).append(
                {
                    "locator": cells[1],
                    "meaning": cells[2],
                    "concepts": sorted({item["label"] for item in concept_links}),
                    "concept_links": concept_links,
                    "concept_cell": cells[3],
                    "disposition": cells[4].strip().lower(),
                    "ledger_page": rel,
                }
            )
        page_categories = {
            active_categories[source_id]
            for source_id in page_source_ids
            if source_id in active_categories
        }
        if (
            len(page_categories) > 1
            and not str(metadata.get("cohort_reason") or "").strip()
        ):
            errors.append(
                f"{rel} spans multiple input routes ({', '.join(sorted(page_categories))}); "
                "split it by natural route or add a specific cohort_reason"
            )
        if page_source_ids == set(active_categories) and len(page_categories) > 1:
            errors.append(
                f"{rel} is a monolithic all-source ledger; split source accounting into traversable routes"
            )
    return rows_by_source, errors


def _normalized_coverage_locator(locator: Any) -> str:
    """Normalize only inconsequential locator whitespace and case."""
    return re.sub(r"\s+", " ", str(locator or "").strip()).casefold()


def _source_page_coverage_rows(
    run_dir: Path,
    records: list[dict[str, Any]],
    entities: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Derive captured source coverage from canonical concept Evidence links."""
    rows_by_source: dict[str, list[dict[str, Any]]] = {
        str(record.get("source_id") or ""): [] for record in records
    }
    rows_by_locator: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        source_id = str(record.get("source_id") or "")
        source_page = _safe_run_path(run_dir, str(record.get("page") or ""))
        for entity_id, entity in entities.items():
            for evidence in entity.get("evidence_records") or []:
                if evidence.get("source_id") != source_id:
                    continue
                concept_page = _safe_run_path(run_dir, str(entity.get("page") or ""))
                target = _relative_link(source_page, concept_page)
                if entity.get("anchor"):
                    target += f"#{entity['anchor']}"
                locator = str(evidence.get("locator") or "Document-wide")
                key = (source_id, _normalized_coverage_locator(locator))
                row = rows_by_locator.setdefault(
                    key,
                    {
                        "locator": locator,
                        "meanings": set(),
                        "concepts": [],
                        "concept_links": [],
                        "disposition": "captured",
                        "ledger_page": _relative(run_dir, source_page),
                    },
                )
                row["meanings"].add(str(entity.get("title") or entity_id))
                if entity_id not in row["concepts"]:
                    row["concepts"].append(entity_id)
                    row["concept_links"].append({"label": entity_id, "target": target})
    for (source_id, _locator), row in rows_by_locator.items():
        row["concepts"].sort()
        row["concept_links"].sort(key=lambda item: item["label"])
        row["meaning"] = "; ".join(sorted(row.pop("meanings")))
        row["concept_cell"] = ", ".join(
            f"[{item['label']}]({item['target']})" for item in row["concept_links"]
        )
        rows_by_source[source_id].append(row)
    for rows in rows_by_source.values():
        rows.sort(key=lambda row: _normalized_coverage_locator(row["locator"]))
    return rows_by_source, []


def _resolved_source_coverage_rows(
    run_dir: Path,
    records: list[dict[str, Any]],
    entities: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[str], int, int]:
    """Combine canonical captured Evidence with model-authored exceptions."""
    resolved, errors = _source_page_coverage_rows(run_dir, records, entities)
    authored, ledger_errors = _coverage_ledger_rows(run_dir)
    errors.extend(ledger_errors)
    legacy_captured_rows = 0
    exception_rows = 0

    for source_id, rows in authored.items():
        canonical_by_locator = {
            _normalized_coverage_locator(row.get("locator")): row
            for row in resolved.get(source_id, [])
        }
        canonical_source_concepts = {
            concept
            for canonical_row in canonical_by_locator.values()
            for concept in (canonical_row.get("concepts") or [])
        }
        exception_locators: set[str] = set()
        for row in rows:
            locator_key = _normalized_coverage_locator(row.get("locator"))
            canonical = canonical_by_locator.get(locator_key)
            disposition = str(row.get("disposition") or "")
            if disposition == "captured":
                legacy_captured_rows += 1
                if (
                    not row.get("concepts")
                    or not set(row["concepts"]) <= canonical_source_concepts
                ):
                    errors.append(
                        f"{source_id} coverage locator {row.get('locator')} uses a legacy captured row "
                        "without equivalent canonical concept Evidence for that source"
                    )
                continue
            if locator_key in exception_locators:
                errors.append(
                    f"duplicate coverage locator: {source_id} {row.get('locator')}"
                )
                continue
            exception_locators.add(locator_key)
            exception_rows += 1
            concept_exception = disposition in {
                "contradiction",
                "duplicate",
                "superseded",
            }
            if canonical and not concept_exception:
                errors.append(
                    f"{source_id} coverage locator {row.get('locator')} is both concept Evidence "
                    f"and {disposition}"
                )
                continue
            if concept_exception:
                evidence_concepts = set((canonical or {}).get("concepts") or [])
                if (
                    not canonical
                    or not set(row.get("concepts") or []) <= evidence_concepts
                ):
                    errors.append(
                        f"{source_id} coverage locator {row.get('locator')} {disposition} links concepts "
                        "not backed by canonical Evidence at that locator"
                    )
                    continue
            canonical_by_locator[locator_key] = row
        resolved[source_id] = sorted(
            canonical_by_locator.values(),
            key=lambda item: _normalized_coverage_locator(item.get("locator")),
        )
    return resolved, errors, legacy_captured_rows, exception_rows


def _validate_source_coverage(
    run_dir: Path,
    entities: dict[str, dict[str, Any]],
) -> tuple[list[str], dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Resolve and validate canonical captured coverage plus exceptions."""
    state = _load_state(run_dir)
    active_records = [
        record
        for record in (state.get("sources") or {}).values()
        if isinstance(record, dict)
        and record.get("semantic")
        and record.get("current_sha256") is not None
    ]
    errors: list[str] = []
    ledger_pages = _coverage_pages(run_dir)
    rows_by_source, ledger_errors, legacy_captured_rows, exception_rows = (
        _resolved_source_coverage_rows(run_dir, active_records, entities)
    )
    errors.extend(ledger_errors)
    active_sources = 0
    row_count = 0
    for record in active_records:
        active_sources += 1
        source_id = str(record.get("source_id") or "")
        page = _safe_run_path(run_dir, str(record.get("page") or ""))
        rows = rows_by_source.get(source_id, [])
        rows_by_source[source_id] = rows
        row_count += len(rows)
        if not rows:
            errors.append(
                f"{source_id} has no concept Evidence or exception coverage rows"
            )
            continue
        for row in rows:
            if row["disposition"] not in COVERAGE_DISPOSITIONS:
                errors.append(
                    f"{source_id} coverage locator {row['locator']} has unsupported disposition {row['disposition']}"
                )
            unknown = sorted(set(row["concepts"]) - set(entities))
            if unknown:
                errors.append(
                    f"{source_id} coverage locator {row['locator']} references unknown concepts: "
                    + ", ".join(unknown)
                )
            for link in row["concept_links"]:
                target_text = str(link["target"]).partition("#")[0].strip().strip("<>")
                if " " in target_text:
                    target_text = target_text.split()[0]
                if not Path(unquote(target_text)).suffix:
                    target_text += ".md"
                link_base = (
                    _safe_run_path(run_dir, str(row.get("ledger_page"))).parent
                    if row.get("ledger_page")
                    else page.parent
                )
                target = (link_base / unquote(target_text)).resolve()
                expected = entities.get(link["label"], {}).get("page")
                if (
                    expected
                    and target != _safe_run_path(run_dir, str(expected)).resolve()
                ):
                    errors.append(
                        f"{source_id} coverage label {link['label']} points to the wrong concept page"
                    )
            if (
                row["disposition"]
                in {"captured", "contradiction", "duplicate", "superseded"}
                and not row["concepts"]
            ):
                errors.append(
                    f"{source_id} coverage locator {row['locator']} disposition {row['disposition']} needs a concept link"
                )

    active_source_ids = {
        str(record.get("source_id") or "") for record in active_records
    }
    stale_sources = sorted(set(rows_by_source) - active_source_ids)
    if stale_sources:
        errors.append(
            "coverage ledgers reference inactive sources: " + ", ".join(stale_sources)
        )

    captured_rows = sum(
        row.get("disposition") == "captured"
        for rows in rows_by_source.values()
        for row in rows
    )
    return (
        errors,
        {
            "mode": "concept-evidence-plus-exceptions",
            "sources": active_sources,
            "rows": row_count,
            "captured_rows": captured_rows,
            "exception_rows": exception_rows,
            "legacy_captured_rows": legacy_captured_rows,
            "accounted_sources": sum(
                bool(rows_by_source.get(source_id)) for source_id in active_source_ids
            ),
            "coverage_pages": len(ledger_pages),
        },
        rows_by_source,
    )


def _validate_okf_bundle(
    run_dir: Path,
    pages: list[Path] | None = None,
    *,
    require_root: bool = True,
) -> list[str]:
    """Apply a strict producer profile on top of OKF's permissive consumer spec."""
    errors: list[str] = []
    knowledge = _safe_run_path(run_dir, KNOWLEDGE_PATH)
    if require_root:
        root_index = knowledge / "index.md"
        try:
            metadata, _body = _frontmatter(_read_text(root_index))
            if str(metadata.get("okf_version") or "") != OKF_VERSION:
                errors.append(
                    f"{_relative(run_dir, root_index)} must declare okf_version {OKF_VERSION}"
                )
        except (KnowledgeError, OSError) as exc:
            errors.append(f"{_relative(run_dir, root_index)}: {exc}")

    topic_pages = set(_topic_pages(run_dir))
    for page in pages if pages is not None else _all_knowledge_pages(run_dir):
        if page.name in {"index.md", "log.md"}:
            continue
        rel = _relative(run_dir, page)
        try:
            metadata, _body = _frontmatter(_read_text(page))
        except KnowledgeError as exc:
            errors.append(f"{rel}: {exc}")
            continue
        for field in CONCEPT_REQUIRED_FIELDS:
            if not str(metadata.get(field) or "").strip():
                errors.append(f"{rel} needs non-empty frontmatter field: {field}")
        tags = metadata.get("tags")
        if tags is not None and (
            not isinstance(tags, list) or any(not str(tag).strip() for tag in tags)
        ):
            errors.append(f"{rel} frontmatter tags must be a list of non-empty values")
        resource = metadata.get("resource")
        if resource is not None and not str(resource).strip():
            errors.append(f"{rel} frontmatter resource must be non-empty when present")
        if (
            page.parent.name == "sources"
            and metadata.get("type") != "Requirements Source"
        ):
            errors.append(f"{rel} type must be 'Requirements Source'")
        canonical_id = str(metadata.get("canonical_id") or "").strip()
        concept_type = str(metadata.get("type") or "").strip()
        if (
            page in topic_pages
            and concept_type == "Requirements Collection"
            and canonical_id
        ):
            errors.append(
                f"{rel} Requirements Collection must omit page-level canonical_id; "
                "give each H2 entity its own graph-safe ID and per-node metadata"
            )
        if page in topic_pages and canonical_id:
            if concept_type in {"Requirements Topic", "Knowledge Concept"}:
                errors.append(f"{rel} needs a specific evidence-backed concept type")
            for field in KNOWLEDGE_REQUIRED_FIELDS:
                value = metadata.get(field)
                if value is None or value == "" or value == []:
                    errors.append(f"{rel} needs non-empty producer field: {field}")
            if not ENTITY_ID_RE.fullmatch(canonical_id):
                errors.append(
                    f"{rel} canonical_id is invalid: {canonical_id}; use uppercase "
                    "hyphen-separated segments ending in 1-8 digits (for example KPI-001)"
                )
            status = str(metadata.get("status") or "").strip().lower()
            if status not in KNOWLEDGE_STATUSES:
                errors.append(f"{rel} has unsupported status: {status or '<empty>'}")
            confidence = str(metadata.get("confidence") or "").strip().lower()
            if confidence not in KNOWLEDGE_CONFIDENCE:
                errors.append(
                    f"{rel} has unsupported confidence: {confidence or '<empty>'}"
                )
            outputs = metadata.get("outputs")
            if not isinstance(outputs, list) or any(
                str(value).upper() not in _outputs_by_id() for value in outputs
            ):
                errors.append(f"{rel} outputs must be a list of known deliverable IDs")
    return errors


def _parse_relations(section: str) -> tuple[list[dict[str, str]], list[str]]:
    heading = RELATIONS_HEADING_RE.search(section)
    if not heading:
        return [], []
    relations: list[dict[str, str]] = []
    errors: list[str] = []
    for match in RELATION_LINE_RE.finditer(section[heading.end() :]):
        kind = match.group("kind")
        if kind not in RELATION_TYPES:
            errors.append(f"unknown relationship type: {kind}")
            continue
        targets = list(dict.fromkeys(ENTITY_ID_RE.findall(match.group("targets"))))
        if not targets:
            errors.append(
                f"relationship {kind} has no graph-safe entity target; link an existing "
                "uppercase canonical ID ending in 1-8 digits"
            )
            continue
        relations.extend({"type": kind, "target": target} for target in targets)
    return relations, errors


def _graph_errors(entities: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for relation_type in ACYCLIC_RELATION_TYPES:
        adjacency = {
            entity_id: [
                edge["target"]
                for edge in item.get("relations") or []
                if edge.get("type") == relation_type and edge.get("target") in entities
            ]
            for entity_id, item in entities.items()
        }
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(entity_id: str, trail: list[str]) -> None:
            if entity_id in visiting:
                start = trail.index(entity_id) if entity_id in trail else 0
                errors.append(
                    f"{relation_type} relationship cycle: "
                    + " -> ".join([*trail[start:], entity_id])
                )
                return
            if entity_id in visited:
                return
            visiting.add(entity_id)
            for target in adjacency.get(entity_id, []):
                visit(target, [*trail, entity_id])
            visiting.remove(entity_id)
            visited.add(entity_id)

        for entity_id in adjacency:
            visit(entity_id, [])
    return list(dict.fromkeys(errors))


def _normative_obligation_count(section: str) -> int:
    """Count obligations only in the entity's normative statement.

    Evidence, verification, relations, examples, and table explanations can
    legitimately repeat SHALL while describing or testing one obligation.  A
    collection entity has no required Statement heading, so its whole section
    remains the conservative default.
    """
    statement = re.search(
        r"(?ms)^#{2,6}\s+Statement\s*\n(?P<body>.*?)(?=^#{2,6}\s+|\Z)",
        section,
    )
    normative_text = statement.group("body") if statement else section
    return len(re.findall(r"\bSHALL\b", normative_text, re.IGNORECASE))


def _parse_entities(
    run_dir: Path,
    pages: list[Path] | None = None,
    *,
    validate_graph: bool = True,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    valid_outputs = set(_outputs_by_id())
    selected_outputs = set(_load_state(run_dir).get("selected_outputs") or [])
    entities: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for page in pages if pages is not None else _topic_pages(run_dir):
        text = _read_text(page)
        try:
            metadata, body = _frontmatter(text)
        except KnowledgeError:
            metadata, body = {}, text
        collection_page = (
            str(metadata.get("type") or "").strip() == "Requirements Collection"
        )
        canonical_id = str(metadata.get("canonical_id") or "").strip()
        if canonical_id:
            deliverables = list(
                dict.fromkeys(
                    str(value).upper()
                    for value in (metadata.get("outputs") or [])
                    if str(value).upper() in valid_outputs
                )
            )
            rel = _relative(run_dir, page)
            if canonical_id in entities:
                errors.append(
                    f"duplicate entity {canonical_id}: {entities[canonical_id]['page']} and {rel}"
                )
                continue
            if canonical_id.lower() not in _heading_anchors(body):
                errors.append(
                    f"{rel} needs an H1 heading beginning with {canonical_id}"
                )
            if not deliverables:
                errors.append(f"{rel}#{canonical_id} needs non-empty outputs metadata")
            unexpected = sorted(set(deliverables) - selected_outputs)
            if unexpected:
                errors.append(
                    f"{rel}#{canonical_id} references unselected deliverables: "
                    + ", ".join(unexpected)
                )
            evidence_records, evidence_errors = _source_evidence_records(
                body, page, run_dir
            )
            errors.extend(f"{rel}#{canonical_id} {error}" for error in evidence_errors)
            status = str(metadata.get("status") or "").strip().lower()
            if not evidence_records and status not in {
                "assumption",
                "insufficient",
                "draft",
            }:
                errors.append(
                    f"{rel}#{canonical_id} needs source evidence or assumption/insufficient status"
                )
            relations, relation_errors = _parse_relations(body)
            errors.extend(f"{rel}#{canonical_id} {error}" for error in relation_errors)
            concept_type = str(metadata.get("type") or "").strip()
            if (
                "requirement" in concept_type.lower()
                and "use case" not in concept_type.lower()
                and not canonical_id.startswith("UC-FR-")
                and _normative_obligation_count(body) > 1
            ):
                errors.append(
                    f"{rel}#{canonical_id} contains multiple SHALL obligations; split independently verifiable requirements"
                )
            semantic_metadata = {
                key: metadata.get(key)
                for key in ("type", "status", "confidence", "standalone_reason")
                if metadata.get(key) is not None
            }
            entities[canonical_id] = {
                "page": rel,
                "anchor": canonical_id.lower(),
                "start_line": text.count("\n", 0, text.find(body)) + 1,
                "line_count": body.count("\n") + 1,
                "title": str(metadata.get("title") or "").strip(),
                "type": concept_type,
                "status": status,
                "confidence": str(metadata.get("confidence") or "unknown").lower(),
                "deliverables": deliverables,
                "relations": relations,
                "evidence": sorted({item["source_id"] for item in evidence_records}),
                "evidence_records": evidence_records,
                "source_status": status,
                "first_class": True,
                "standalone_reason": str(
                    metadata.get("standalone_reason") or ""
                ).strip(),
                "content_sha256": _sha_text(
                    json.dumps(semantic_metadata, ensure_ascii=False, sort_keys=True)
                    + "\n"
                    + body.strip()
                ),
                "sha256": _sha_text(
                    json.dumps(metadata, ensure_ascii=False, sort_keys=True)
                    + "\n"
                    + body
                ),
            }
            continue
        headings = list(ENTITY_HEADING_RE.finditer(text))
        if not headings and "<!-- SUPPORT-PAGE -->" not in text:
            errors.append(
                f"{_relative(run_dir, page)} contains no recognized entity headings; "
                "use a stable compound ID such as R-GEN-001 or mark a non-entity page <!-- SUPPORT-PAGE -->"
            )
        for index, match in enumerate(headings):
            start = match.start()
            end = (
                headings[index + 1].start() if index + 1 < len(headings) else len(text)
            )
            section = text[start:end].strip() + "\n"
            entity_id = match.group("id")
            if entity_id in entities:
                errors.append(
                    f"duplicate entity {entity_id}: {entities[entity_id]['page']} and {_relative(run_dir, page)}"
                )
                continue
            deliverables = _parse_deliverables(section, valid_outputs)
            if not deliverables:
                errors.append(
                    f"{_relative(run_dir, page)}#{entity_id} needs a Markdown line 'Deliverables: <selected IDs>'"
                )
            unexpected = sorted(set(deliverables) - selected_outputs)
            if unexpected:
                errors.append(
                    f"{_relative(run_dir, page)}#{entity_id} references unselected deliverables: "
                    + ", ".join(unexpected)
                )
            explicit_status = _parse_labeled_value(ENTITY_STATUS_RE, section).lower()
            if (
                not _has_source_evidence(section, page, run_dir)
                and explicit_status not in {"assumption", "insufficient", "draft"}
                and not re.search(
                    r"\[(?:ASSUMPTION|INSUFFICIENT INPUT)\]", section, re.IGNORECASE
                )
            ):
                errors.append(
                    f"{_relative(run_dir, page)}#{entity_id} needs a source-page link or an explicit assumption/insufficient-input marker"
                )
            evidence_records, evidence_errors = _source_evidence_records(
                section, page, run_dir
            )
            errors.extend(
                f"{_relative(run_dir, page)}#{entity_id} {error}"
                for error in evidence_errors
            )
            relations, relation_errors = _parse_relations(section)
            errors.extend(
                f"{_relative(run_dir, page)}#{entity_id} {error}"
                for error in relation_errors
            )
            entity_type = _parse_labeled_value(ENTITY_TYPE_RE, section)
            status = explicit_status
            confidence = _parse_labeled_value(ENTITY_CONFIDENCE_RE, section).lower()
            standalone_reason = _parse_labeled_value(STANDALONE_REASON_RE, section)
            if collection_page:
                if not entity_type:
                    errors.append(
                        f"{_relative(run_dir, page)}#{entity_id} needs a Type line"
                    )
                if status not in KNOWLEDGE_STATUSES:
                    errors.append(
                        f"{_relative(run_dir, page)}#{entity_id} has unsupported status: {status or '<empty>'}"
                    )
                if confidence not in KNOWLEDGE_CONFIDENCE:
                    errors.append(
                        f"{_relative(run_dir, page)}#{entity_id} has unsupported confidence: {confidence or '<empty>'}"
                    )
                if (
                    "requirement" in entity_type.lower()
                    and "use case" not in entity_type.lower()
                    and not entity_id.startswith("UC-FR-")
                    and _normative_obligation_count(section) > 1
                ):
                    errors.append(
                        f"{_relative(run_dir, page)}#{entity_id} contains multiple SHALL obligations; split independently verifiable requirements"
                    )
            start_line = text.count("\n", 0, start) + 1
            entities[entity_id] = {
                "page": _relative(run_dir, page),
                "anchor": entity_id.lower(),
                "start_line": start_line,
                "line_count": section.count("\n") + 1,
                "type": entity_type
                or str(metadata.get("type") or "Requirements Topic"),
                "status": status or "grounded",
                "confidence": confidence or "unknown",
                "title": match.group("title").strip(" -—–"),
                "deliverables": deliverables,
                "relations": relations,
                "evidence": sorted({item["source_id"] for item in evidence_records}),
                "evidence_records": evidence_records,
                "first_class": False,
                "collection_entity": collection_page,
                "standalone_reason": standalone_reason,
                "source_status": (
                    "insufficient"
                    if re.search(r"\[INSUFFICIENT INPUT\]", section, re.IGNORECASE)
                    else "assumption"
                    if re.search(r"\[ASSUMPTION\]", section, re.IGNORECASE)
                    else "grounded"
                ),
                "content_sha256": _sha_text(
                    re.sub(
                        r"(?m)^\s*---\s*$",
                        "",
                        re.sub(
                            r"(?im)^\s*(?:-\s*)?Deliverables\s*:\s*.*$",
                            "",
                            section,
                        ),
                    ).strip()
                ),
                "sha256": _sha_text(section),
            }
    if validate_graph:
        for entity_id, entity in entities.items():
            for relation in entity.get("relations") or []:
                target = relation["target"]
                if target not in entities:
                    errors.append(
                        f"{entity['page']}#{entity_id} relationship {relation['type']} "
                        f"targets unknown entity {target}"
                    )
        errors.extend(_graph_errors(entities))
        incoming = {entity_id: 0 for entity_id in entities}
        for entity in entities.values():
            for relation in entity.get("relations") or []:
                if relation.get("target") in incoming:
                    incoming[relation["target"]] += 1
        for entity_id, entity in entities.items():
            if (
                (entity.get("first_class") or entity.get("collection_entity"))
                and not entity.get("relations")
                and incoming.get(entity_id, 0) == 0
                and not entity.get("standalone_reason")
            ):
                errors.append(
                    f"{entity['page']}#{entity_id} is an orphan concept; add a meaningful "
                    "relation or standalone_reason"
                )
    else:
        for entity_id, entity in entities.items():
            if not entity.get("relations") and not entity.get("standalone_reason"):
                errors.append(
                    f"{entity['page']}#{entity_id} has no outbound relation; add a "
                    "meaningful relation or standalone_reason before merge"
                )
    return entities, errors


def _heading_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        heading = re.sub(r"[`*_~]", "", match.group(1)).strip().lower()
        # GitHub-style Markdown anchors preserve literal hyphens and replace
        # each whitespace character with one hyphen.  Do not collapse the
        # resulting run: ``KPI-001 - Name`` is ``kpi-001---name``.
        anchor = re.sub(r"[^\w\- ]", "", heading, flags=re.UNICODE)
        anchor = re.sub(r"\s", "-", anchor).strip("-")
        if anchor:
            anchors.add(anchor)
        id_match = re.match(
            r"([A-Z][A-Z0-9]{0,11}(?:-[A-Z][A-Z0-9]{0,11})*-\d{1,8})\b",
            match.group(1),
        )
        if id_match:
            anchors.add(id_match.group(1).lower())
    return anchors


def _canonicalize_entity_link_anchors(
    run_dir: Path,
    entities: dict[str, dict[str, Any]],
) -> int:
    """Replace fragile title slugs with stable canonical-ID fragments.

    This changes no semantic text.  A link is eligible only when its visible
    label is a known entity ID and its resolved file is that entity's actual
    page, so an incorrect path is still rejected by normal link validation.
    """
    changed_pages = 0
    entity_link = re.compile(
        r"\[(?P<label>[A-Z][A-Z0-9]{0,11}(?:-[A-Z][A-Z0-9]{0,11})*-\d{1,8})\]"
        r"\((?P<target>[^)]+)\)"
    )
    for page in _topic_pages(run_dir) + _coverage_pages(run_dir):
        text = _read_text(page)

        def replace(match: re.Match[str]) -> str:
            entity_id = match.group("label")
            entity = entities.get(entity_id)
            if not entity:
                return match.group(0)
            target = match.group("target").strip()
            path_text, separator, fragment = target.partition("#")
            if not separator or not fragment or fragment.lower() == entity_id.lower():
                return match.group(0)
            if not fragment.lower().startswith(entity_id.lower() + "-"):
                return match.group(0)
            resolved = (
                page.resolve()
                if not path_text
                else (page.parent / unquote(path_text.strip().strip("<>"))).resolve()
            )
            expected = _safe_run_path(run_dir, str(entity["page"])).resolve()
            if resolved != expected:
                return match.group(0)
            canonical_target = f"{path_text}#{entity_id.lower()}"
            return f"[{entity_id}]({canonical_target})"

        normalized = entity_link.sub(replace, text)
        if normalized != text:
            _write_if_changed(page, normalized)
            changed_pages += 1
    return changed_pages


def normalize_entity_links(run_dir: Path) -> dict[str, Any]:
    """Normalize resolvable entity links to stable ID fragments before merge.

    Authors remain responsible for paths and entity identity. This only replaces
    a title-derived fragment when the visible label, resolved file, and known
    canonical entity all agree.
    """
    entities, _errors = _parse_entities(run_dir, validate_graph=False)
    changed_pages = _canonicalize_entity_link_anchors(run_dir, entities)
    return {
        "changed_pages": changed_pages,
        "known_entities": len(entities),
    }


def _link_targets(text: str) -> list[str]:
    targets = [
        match.group("target").strip() for match in MARKDOWN_LINK_RE.finditer(text)
    ]
    targets.extend(
        match.group("target").strip() for match in WIKI_LINK_RE.finditer(text)
    )
    return targets


def validate_links(run_dir: Path) -> list[str]:
    errors: list[str] = []
    for page in _all_knowledge_pages(run_dir):
        text = _read_text(page)
        for raw_target in _link_targets(text):
            target = raw_target.strip().strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if " " in target and not target.startswith("#"):
                target = target.split()[0]
            file_part, separator, anchor = target.partition("#")
            if target.startswith("[["):
                continue
            if not file_part:
                target_path = page
            else:
                decoded = unquote(file_part)
                if not Path(decoded).suffix:
                    decoded += ".md"
                target_path = (page.parent / decoded).resolve()
            try:
                target_path.relative_to(run_dir.resolve())
            except ValueError:
                errors.append(
                    f"{_relative(run_dir, page)} has link escaping run: {raw_target}"
                )
                continue
            if not target_path.is_file():
                if page.name == "log.md":
                    # Historical entries intentionally retain links to concepts
                    # that a later semantic update removed.
                    continue
                errors.append(
                    f"{_relative(run_dir, page)} has missing link target: {raw_target}"
                )
                continue
            if separator and anchor:
                normalized = unquote(anchor).strip().lower()
                if normalized and normalized not in _heading_anchors(
                    _read_text(target_path)
                ):
                    errors.append(
                        f"{_relative(run_dir, page)} has missing anchor: {raw_target}"
                    )
    return errors


def _backlinks(run_dir: Path, target: str) -> list[str]:
    normalized = target.replace("\\", "/")
    target_name = Path(normalized).name
    results = []
    for page in _all_knowledge_pages(run_dir):
        text = _read_text(page).replace("\\", "/")
        if normalized in text or target_name in text:
            rel = _relative(run_dir, page)
            if rel != normalized:
                results.append(rel)
    return sorted(set(results))


def plan_extract(run_dir: Path) -> dict[str, Any]:
    state = _load_state(run_dir)
    if (state.get("phases", {}).get("start") or {}).get("status") != "complete":
        raise KnowledgeError("/start-run must commit before extraction")
    changed_sources: list[dict[str, Any]] = []
    impacted_topics: set[str] = set()
    for record in state.get("sources", {}).values():
        if not record.get("semantic"):
            continue
        current = record.get("current_sha256")
        extracted = record.get("extracted_sha256")
        if current is None:
            extraction_status = (
                "unchanged"
                if record.get("extraction_deletion_committed")
                else "deleted"
            )
        elif extracted is None:
            extraction_status = "added"
        elif extracted != current:
            extraction_status = "modified"
        else:
            extraction_status = "unchanged"
        if extraction_status == "unchanged":
            continue
        page = record.get("page")
        if page:
            changed_sources.append(
                {
                    "source_id": record.get("source_id"),
                    "status": extraction_status,
                    "path": record.get("path"),
                    "read_path": record.get("text_path") or record.get("path"),
                    "page": page,
                }
            )
            for backlink in _backlinks(run_dir, page):
                if backlink in {
                    _relative(run_dir, concept) for concept in _topic_pages(run_dir)
                }:
                    impacted_topics.add(backlink)
    first_extract = not bool((state.get("knowledge") or {}).get("entity_hashes"))
    if first_extract:
        impacted_topics.update(
            _relative(run_dir, path) for path in _topic_pages(run_dir)
        )
    overview = source_overview(run_dir, "extract")
    return {
        "mode": "full" if first_extract else "targeted",
        "fresh_graph": first_extract,
        "authoring_strategy": "single-curator",
        "authoring_strategy_reason": (
            "one cross-source owner preserves semantic synthesis, deduplication, and stable IDs"
        ),
        "selected_outputs": list(state.get("selected_outputs") or []),
        "knowledge_index": f"{KNOWLEDGE_PATH.as_posix()}/index.md",
        "changed_source_characters": overview["total_characters"],
        "source_routing": overview["sources"],
        "changed_sources": sorted(
            changed_sources, key=lambda item: str(item["source_id"])
        ),
        "changed_source_pages": sorted(str(item["page"]) for item in changed_sources),
        "impacted_topic_pages": sorted(impacted_topics),
        "impacted_concept_pages": sorted(impacted_topics),
    }


def commit_start(run_dir: Path, selected: list[str]) -> dict[str, Any]:
    state = _load_state(run_dir)
    _render_source_nodes_and_index(run_dir, state)
    valid = set(_outputs_by_id())
    normalized = []
    for value in selected:
        code = value.upper()
        if code not in valid:
            raise KnowledgeError(f"unknown deliverable: {value}")
        if code not in normalized:
            normalized.append(code)

    report = _safe_run_path(run_dir, INPUT_REPORT_PATH)
    report_errors = _input_report_spine_errors(report)
    if report_errors:
        raise KnowledgeError(
            "input evaluation report validation failed:\n- "
            + "\n- ".join(report_errors)
        )
    missing_pages = []
    semantic_changed = False
    control_changed = False
    for record in state.get("sources", {}).values():
        if record.get("status") == "unchanged":
            continue
        if record.get("semantic"):
            semantic_changed = True
            page = record.get("page")
            if page and not _safe_run_path(run_dir, page).is_file():
                missing_pages.append(page)
        else:
            control_changed = True
    if missing_pages:
        raise KnowledgeError(
            "missing source knowledge pages: " + ", ".join(sorted(missing_pages))
        )

    prior_selection = list(state.get("selected_outputs") or [])
    state["selected_outputs"] = normalized
    state["input_report_template_sha256"] = _input_report_template_sha256()
    for record in state.get("sources", {}).values():
        record["committed_sha256"] = record.get("current_sha256")
        record["deletion_committed"] = record.get("current_sha256") is None
    state["phases"]["start"] = {"status": "complete", "completed_at": _now()}
    if semantic_changed:
        state["phases"]["extract"] = {"status": "dirty"}
        state["extraction"] = {"status": "dirty"}
    invalidates_downstream = (
        semantic_changed or control_changed or prior_selection != normalized
    )
    if control_changed or prior_selection != normalized:
        for code in normalized:
            state.setdefault("generation_summary", {}).setdefault(code, {})[
                "status"
            ] = "dirty"
    for code in valid - set(normalized):
        state.setdefault("generation_summary", {}).setdefault(code, {})["status"] = (
            "skipped"
        )
    if invalidates_downstream:
        state["phases"]["evaluate"] = {"status": "dirty"}
        state["evaluation"] = {"status": "dirty"}
    _save_state(run_dir, state)
    return {
        "selected_outputs": normalized,
        "semantic_sources_changed": semantic_changed,
        "control_inputs_changed": control_changed,
        "report": INPUT_REPORT_PATH.as_posix(),
    }


def _append_knowledge_log(
    run_dir: Path,
    entities: dict[str, dict[str, Any]],
    changed: list[str],
    deleted: list[str],
) -> None:
    if not changed and not deleted:
        return
    knowledge = _safe_run_path(run_dir, KNOWLEDGE_PATH)
    log = knowledge / "log.md"
    date = _now()[:10]
    links = []
    for entity_id in changed:
        item = entities.get(entity_id)
        if not item:
            continue
        target = _safe_run_path(run_dir, str(item["page"]))
        anchor = str(item.get("anchor") or "")
        href = _relative_link(log, target) + (f"#{anchor}" if anchor else "")
        links.append(f"[{entity_id}]({href})")
    details = ", ".join(links) if links else "no surviving concepts"
    if deleted:
        details += "; removed " + ", ".join(deleted)
    fingerprint = _sha_text("|".join([*changed, "--", *deleted]))[:12]
    entry = (
        f"* **Update**: Semantic extraction committed {len(changed)} changed and "
        f"{len(deleted)} removed concepts — {details}. `change:{fingerprint}`"
    )
    existing = (
        log.read_text(encoding="utf-8")
        if log.is_file()
        else "# Requirements Knowledge Update Log\n"
    )
    if f"change:{fingerprint}" in existing:
        return
    heading = f"## {date}"
    if heading in existing:
        existing = existing.replace(heading, f"{heading}\n{entry}", 1)
    else:
        title, _, remainder = existing.partition("\n")
        existing = f"{title}\n\n{heading}\n{entry}\n" + remainder.lstrip("\n")
    _write_if_changed(log, existing.rstrip() + "\n")


def commit_extract(run_dir: Path) -> dict[str, Any]:
    state = _load_state(run_dir)
    old_entities = dict((state.get("knowledge") or {}).get("entities") or {})
    entities, entity_errors = _parse_entities(run_dir)
    if _canonicalize_entity_link_anchors(run_dir, entities):
        entities, entity_errors = _parse_entities(run_dir)
    coverage_errors, coverage, coverage_rows = _validate_source_coverage(
        run_dir, entities
    )
    # Source pages always project the resolved canonical Evidence plus exceptions.
    _render_source_nodes_and_index(run_dir, state, coverage_rows, entities)
    link_errors = validate_links(run_dir)
    errors = [
        *_validate_okf_bundle(run_dir),
        *entity_errors,
        *link_errors,
        *coverage_errors,
    ]
    if errors:
        raise KnowledgeError(
            f"knowledge validation failed ({len(errors)} errors):\n- "
            + "\n- ".join(errors)
        )
    if not entities and not old_entities:
        raise KnowledgeError("knowledge/topics contains no requirement entities")

    old_hashes = dict((state.get("knowledge") or {}).get("entity_hashes") or {})
    new_hashes = {entity_id: item["sha256"] for entity_id, item in entities.items()}
    changed = []
    for entity_id in sorted(set(old_hashes) | set(new_hashes)):
        old_entity = old_entities.get(entity_id)
        new_entity = entities.get(entity_id)
        if not old_entity or not new_entity:
            changed.append(entity_id)
            continue
        if old_entity.get("content_sha256") != new_entity.get(
            "content_sha256"
        ) or sorted(old_entity.get("deliverables") or []) != sorted(
            new_entity.get("deliverables") or []
        ):
            changed.append(entity_id)
    deleted = sorted(set(old_hashes) - set(new_hashes))
    _append_knowledge_log(run_dir, entities, changed, deleted)
    page_hashes = {
        _relative(run_dir, page): _sha_file(page)
        for page in _all_knowledge_pages(run_dir)
    }
    knowledge = state.setdefault("knowledge", {})
    knowledge.update(
        {
            "page_hashes": page_hashes,
            "entity_hashes": new_hashes,
            "entities": entities,
            "changed_entities": changed,
            "deleted_entities": deleted,
            "committed_at": _now(),
        }
    )
    selected = set(state.get("selected_outputs") or [])
    for code in selected:
        relevant = []
        for entity_id in changed:
            old_entity = old_entities.get(entity_id) or {}
            new_entity = entities.get(entity_id) or {}
            old_outputs = set(old_entity.get("deliverables") or [])
            new_outputs = set(new_entity.get("deliverables") or [])
            old_content = old_entity.get("content_sha256")
            new_content = new_entity.get("content_sha256")
            if not old_entity or not new_entity or not old_content:
                affected_outputs = old_outputs | new_outputs
            elif old_content != new_content:
                affected_outputs = old_outputs | new_outputs
            else:
                # A Deliverables-only edit changes routing, not prose. Existing
                # outputs remain valid; only newly added or removed outputs are
                # invalidated.
                affected_outputs = old_outputs ^ new_outputs
            if code in affected_outputs:
                relevant.append(entity_id)
        entry = state.setdefault("generation_summary", {}).setdefault(code, {})
        unresolved = sorted(set(entry.get("dirty_entities") or []) | set(relevant))
        entry["dirty_entities"] = unresolved
        if unresolved or entry.get("status") != "complete":
            entry["status"] = "dirty"
    state["phases"]["extract"] = {"status": "complete", "completed_at": _now()}
    state["extraction"] = {
        "status": "complete",
        "entity_count": len(entities),
        "changed_entity_count": len(changed),
    }
    state["phases"]["evaluate"] = {"status": "dirty"}
    state["evaluation"] = {"status": "dirty"}
    for record in state.get("sources", {}).values():
        if not record.get("semantic"):
            continue
        record["extracted_sha256"] = record.get("current_sha256")
        record["extraction_deletion_committed"] = record.get("current_sha256") is None
    _save_state(run_dir, state)
    return {
        "entity_count": len(entities),
        "changed_entity_count": len(changed),
        "deleted_entity_count": len(deleted),
        "topic_pages": len(_topic_pages(run_dir)),
        "concept_pages": len(_topic_pages(run_dir)),
        "source_coverage": coverage,
        "link_errors": 0,
    }


def _output_config(deliverable: str) -> dict[str, Any]:
    code = deliverable.upper()
    output = _outputs_by_id().get(code)
    if not output:
        raise KnowledgeError(f"unknown deliverable: {deliverable}")
    return output


def _template_candidates(run_dir: Path, deliverable: str) -> list[dict[str, str]]:
    output = _output_config(deliverable)
    stems = {str(value).lower() for value in (output.get("stems") or [])}
    stems.add(deliverable.lower())
    candidates: list[dict[str, str]] = []
    manifest_rows = _load_inputs_manifest(run_dir)
    for row in manifest_rows:
        path = str(row.get("path") or "").replace("\\", "/")
        if not path.lower().startswith("inputs/templates/"):
            continue
        haystack = Path(path).stem.lower()
        if not any(stem in haystack for stem in stems):
            continue
        extraction = (
            row.get("extraction") if isinstance(row.get("extraction"), dict) else {}
        )
        candidates.append(
            {
                "path": path,
                "read_path": str(extraction.get("text_path") or path).replace(
                    "\\", "/"
                ),
            }
        )
    default_template = str(output.get("template") or "").replace("\\", "/")
    if default_template:
        candidates.append({"path": default_template, "read_path": default_template})
    unique: list[dict[str, str]] = []
    seen = set()
    for candidate in candidates:
        if candidate["path"] not in seen:
            seen.add(candidate["path"])
            unique.append(candidate)
    return unique


def _parse_blocks(text: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    blocks: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for start in BLOCK_START_RE.finditer(text):
        block_id = start.group("id")
        if block_id in blocks:
            errors.append(f"duplicate render block: {block_id}")
            continue
        end_marker = BLOCK_END_TEMPLATE.format(block_id=block_id)
        end_index = text.find(end_marker, start.end())
        if end_index < 0:
            errors.append(f"render block has no end marker: {block_id}")
            continue
        body = text[start.end() : end_index].strip("\r\n")
        entities = [
            value.strip()
            for value in (start.group("entities") or "").split(",")
            if value.strip()
        ]
        blocks[block_id] = {
            "entities": entities,
            "sha256": _sha_text(body),
            "declared_sha256": start.group("declared_sha256"),
            "body": body,
            "start": start.start(),
            "body_start": start.end(),
            "body_end": end_index,
            "end": end_index + len(end_marker),
        }
    return blocks, errors


def _mentions_entity(body: str, entity_id: str) -> bool:
    """Match an explicit graph ID without treating a longer ID as the same entity."""
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9_-]){re.escape(entity_id)}(?![A-Za-z0-9_-])",
            body,
        )
    )


def _strip_markers(text: str) -> str:
    return BLOCK_MARKER_RE.sub("", text)


def _pending_document_path(run_dir: Path, output_path: str) -> tuple[Path, str]:
    final = _safe_run_path(run_dir, output_path)
    pending = final.with_name(f".{final.stem}.pending")
    return pending, _relative(run_dir, pending)


def _outside_blocks_signature(text: str, ignored: set[str]) -> str:
    blocks, errors = _parse_blocks(text)
    if errors:
        raise KnowledgeError("invalid render blocks: " + "; ".join(errors))
    masked = text
    for block_id, block in sorted(
        blocks.items(), key=lambda item: item[1]["start"], reverse=True
    ):
        replacement = "" if block_id in ignored else f"\n<!-- RA-BLOCK {block_id} -->\n"
        masked = masked[: block["start"]] + replacement + masked[block["end"] :]
    return _sha_text(masked)


def _normalize_block_markers(text: str) -> str:
    blocks, errors = _parse_blocks(text)
    if errors:
        raise KnowledgeError("invalid render blocks: " + "; ".join(errors))
    normalized = text
    for block_id, block in sorted(
        blocks.items(), key=lambda item: item[1]["start"], reverse=True
    ):
        entities = ",".join(dict.fromkeys(block["entities"]))
        start = (
            f'<!-- RA-BLOCK START id="{block_id}" entities="{entities}" '
            f'sha256="{block["sha256"]}" -->'
        )
        end = BLOCK_END_TEMPLATE.format(block_id=block_id)
        replacement = f"{start}\n{block['body']}\n{end}"
        normalized = (
            normalized[: block["start"]] + replacement + normalized[block["end"] :]
        )
    return normalized


def _entity_sections(run_dir: Path) -> dict[str, str]:
    sections: dict[str, str] = {}
    for page in _topic_pages(run_dir):
        text = _read_text(page)
        try:
            metadata, body = _frontmatter(text)
        except KnowledgeError:
            metadata, body = {}, text
        canonical_id = str(metadata.get("canonical_id") or "").strip()
        if canonical_id:
            sections[canonical_id] = body.strip()
            continue
        headings = list(ENTITY_HEADING_RE.finditer(text))
        for index, match in enumerate(headings):
            end = (
                headings[index + 1].start() if index + 1 < len(headings) else len(text)
            )
            sections[match.group("id")] = text[match.start() : end].strip()
    return sections


def _authoring_entity_section(
    entity_id: str,
    section: str,
    item: dict[str, Any],
) -> str:
    """Render the lossless semantic fields needed for document authoring.

    Source link paths, deliverable-routing metadata, and Markdown anchor URLs
    are useful to the graph validator but duplicate information during normal
    generation. Keep the exact requirement body, evidence IDs, status markers,
    and typed relationship endpoints.
    """
    heading = ENTITY_HEADING_RE.search(section)
    relations_heading = RELATIONS_HEADING_RE.search(section)
    body_start = heading.end() if heading else 0
    body_end = relations_heading.start() if relations_heading else len(section)
    body = section[body_start:body_end]
    body = DELIVERABLES_RE.sub("", body)
    body = re.sub(
        r"^\s*(?:[-*]\s*)?(?:\*\*|__)?Evidence(?:\*\*|__)?\s*:\s*.*$",
        "",
        body,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    body = re.sub(r"(?m)^\s*---\s*$", "", body).strip()
    title = str(item.get("title") or "").strip()
    lines = [f"## {entity_id}" + (f" - {title}" if title else "")]
    evidence = list(item.get("evidence") or [])
    if evidence:
        lines.extend(["", "Evidence IDs: " + ", ".join(evidence)])
    if body:
        lines.extend(["", body])
    relations = list(item.get("relations") or [])
    if relations:
        lines.extend(
            [
                "",
                "Relations: "
                + "; ".join(
                    f"{edge['type']} -> {edge['target']}" for edge in relations
                ),
            ]
        )
    return "\n".join(lines).strip()


def _generation_batches(
    run_dir: Path,
    entities: dict[str, dict[str, Any]],
    entity_ids: list[str],
) -> list[dict[str, Any]]:
    """Partition every authoring entity into bounded, route-local receipts."""
    sections = _entity_sections(run_dir)
    batches: list[dict[str, Any]] = []
    current_entities: list[str] = []
    current_routes: list[str] = []
    current_characters = 0

    def flush() -> None:
        nonlocal current_entities, current_routes, current_characters
        if not current_entities:
            return
        batches.append(
            {
                "id": f"context-{len(batches) + 1:03d}",
                "entities": current_entities,
                "routes": current_routes,
                "estimated_characters": current_characters,
            }
        )
        current_entities = []
        current_routes = []
        current_characters = 0

    for route in _generation_routes(run_dir, entities, entity_ids):
        route_path = str(route["path"])
        for entity_id in route["entities"]:
            section = sections.get(entity_id)
            if not section:
                raise KnowledgeError(f"knowledge section is missing for {entity_id}")
            size = len(
                _authoring_entity_section(
                    entity_id,
                    section,
                    entities.get(entity_id) or {},
                )
            )
            if (
                current_entities
                and current_characters + size > AUTHORING_BATCH_CHAR_BUDGET
            ):
                flush()
            current_entities.append(entity_id)
            if route_path not in current_routes:
                current_routes.append(route_path)
            current_characters += size
            if (
                current_characters >= AUTHORING_BATCH_CHAR_BUDGET
                or len(current_entities) >= AUTHORING_BATCH_ENTITY_LIMIT
            ):
                flush()
    flush()
    return batches


def _entity_neighbors(entities: dict[str, dict[str, Any]], entity_id: str) -> list[str]:
    neighbors = {
        edge["target"]
        for edge in (entities.get(entity_id) or {}).get("relations") or []
        if edge.get("target") in entities
    }
    neighbors.update(
        source_id
        for source_id, item in entities.items()
        for edge in item.get("relations") or []
        if edge.get("target") == entity_id
    )
    return sorted(neighbors)


def _generation_routes(
    run_dir: Path,
    entities: dict[str, dict[str, Any]],
    entity_ids: list[str],
) -> list[dict[str, Any]]:
    by_page: dict[str, list[str]] = {}
    selected = set(entity_ids)
    for entity_id in entity_ids:
        item = entities.get(entity_id) or {}
        page = str(item.get("page") or "")
        if page:
            by_page.setdefault(page, []).append(entity_id)
    routes = []
    for page_path, ids in sorted(by_page.items()):
        page = _safe_run_path(run_dir, page_path)
        related = sorted(
            {
                neighbor
                for entity_id in ids
                for neighbor in _entity_neighbors(entities, entity_id)
                if neighbor not in selected
            }
        )
        routes.append(
            {
                "path": page_path,
                "title": _page_title(page),
                "description": _page_description(page),
                "entities": ids,
                "related_entities": related,
            }
        )
    return routes


def prepare_generation(
    run_dir: Path,
    deliverable: str,
    template: str | None,
    requested_blocks: list[str] | None = None,
    requested_entities: list[str] | None = None,
) -> dict[str, Any]:
    code = deliverable.upper()
    output = _output_config(code)
    state = _load_state(run_dir)
    if code not in (state.get("selected_outputs") or []):
        raise KnowledgeError(f"{code} is not selected")
    if (state.get("extraction") or {}).get("status") != "complete":
        raise KnowledgeError("/extract-requirements must commit before generation")

    candidates = _template_candidates(run_dir, code)
    candidate_paths = [item["path"] for item in candidates]
    run_local_paths = [
        path for path in candidate_paths if path.lower().startswith("inputs/templates/")
    ]
    prior_template = ((state.get("deliverables") or {}).get(code) or {}).get(
        "template_path"
    )
    if template:
        chosen = template
    elif run_local_paths:
        if prior_template in run_local_paths:
            chosen = prior_template
        elif len(run_local_paths) == 1:
            chosen = run_local_paths[0]
        else:
            chosen = None
    elif prior_template in candidate_paths:
        chosen = prior_template
    elif candidates:
        chosen = candidates[0]["path"]
    else:
        chosen = str(output.get("template") or "") or None
    output_path = str(output.get("outputPath") or "")
    if not output_path:
        raise KnowledgeError(f"workflow manifest outputPath is missing for {code}")
    if not chosen and run_local_paths:
        return {
            "deliverable": code,
            "mode": "template_selection",
            "output_path": output_path,
            "template_candidates": [
                item for item in candidates if item["path"] in run_local_paths
            ],
        }
    if chosen:
        chosen_path = _safe_template_path(run_dir, chosen)
        if not chosen_path.is_file():
            raise KnowledgeError(f"template does not exist: {chosen}")
        chosen_hash = _sha_file(chosen_path)
    else:
        chosen_hash = None

    document = _safe_run_path(run_dir, output_path)
    pending_document, pending_path = _pending_document_path(run_dir, output_path)
    pending_document.unlink(missing_ok=True)
    prior = (state.get("deliverables") or {}).get(code) or {}
    summary = state.setdefault("generation_summary", {}).setdefault(code, {})
    dirty_entities = list(summary.get("dirty_entities") or [])
    deleted_entities = sorted(
        set(dirty_entities)
        & set((state.get("knowledge") or {}).get("deleted_entities") or [])
    )

    current_blocks: dict[str, dict[str, Any]] = {}
    block_errors: list[str] = []
    current_text = ""
    if document.is_file():
        current_text = _read_text(document)
        current_blocks, block_errors = _parse_blocks(current_text)
    if block_errors:
        raise KnowledgeError("invalid render blocks: " + "; ".join(block_errors))

    explicit_blocks = sorted(set(requested_blocks or []))
    explicit_entities = sorted(set(requested_entities or []))
    if explicit_entities and not explicit_blocks:
        raise KnowledgeError("--entity requires at least one --block")
    unknown_blocks = sorted(set(explicit_blocks) - set(current_blocks))
    if unknown_blocks:
        raise KnowledgeError("unknown document blocks: " + ", ".join(unknown_blocks))
    if explicit_blocks:
        known_entities = (state.get("knowledge") or {}).get("entities") or {}
        unknown_entities = sorted(set(explicit_entities) - set(known_entities))
        if unknown_entities:
            raise KnowledgeError(
                "unknown knowledge entities: " + ", ".join(unknown_entities)
            )
        inapplicable_entities = sorted(
            entity_id
            for entity_id in explicit_entities
            if code not in (known_entities[entity_id].get("deliverables") or [])
        )
        if inapplicable_entities:
            raise KnowledgeError(
                f"entities are not applicable to {code}: "
                + ", ".join(inapplicable_entities)
            )
        mode = "targeted"
        dirty_entities = explicit_entities or sorted(
            {
                entity_id
                for block_id in explicit_blocks
                for entity_id in current_blocks[block_id].get("entities") or []
            }
        )
        deleted_entities = []
    elif not document.is_file():
        mode = "full"
    elif not current_blocks:
        mode = "marker_migration"
    elif (
        chosen_hash
        and prior.get("template_sha256")
        and chosen_hash != prior.get("template_sha256")
    ):
        mode = "full"
    elif not dirty_entities:
        mode = "no_op"
    else:
        mode = "targeted"

    entities = (state.get("knowledge") or {}).get("entities") or {}
    if mode == "full":
        # A missing document or changed dynamic template is a real full render.
        # Its plan must cover every applicable entity, even when semantic inputs
        # themselves are unchanged.
        dirty_entities = sorted(
            entity_id
            for entity_id, item in entities.items()
            if code in (item.get("deliverables") or [])
        )
        deleted_entities = []

    target_blocks = explicit_blocks or sorted(
        block_id
        for block_id, block in current_blocks.items()
        if set(block.get("entities") or []) & set(dirty_entities)
        or any(
            _mentions_entity(str(block.get("body") or ""), entity_id)
            for entity_id in dirty_entities
        )
    )
    conflicts = sorted(
        block_id
        for block_id in target_blocks
        if (
            current_blocks[block_id].get("declared_sha256")
            and current_blocks[block_id]["sha256"]
            != current_blocks[block_id].get("declared_sha256")
        )
        or (
            not current_blocks[block_id].get("declared_sha256")
            and block_id in (prior.get("blocks") or {})
            and current_blocks[block_id]["sha256"]
            != prior["blocks"][block_id].get("sha256")
        )
    )
    author_path = pending_path
    pending = {
        "mode": mode,
        "author_path": author_path,
        "template_path": chosen,
        "template_sha256": chosen_hash,
        "baseline_document_sha256": _sha_text(current_text) if current_text else None,
        "baseline_without_markers_sha256": _sha_text(_strip_markers(current_text))
        if current_text
        else None,
        "dirty_entities": dirty_entities,
        "deleted_entities": deleted_entities,
        "target_blocks": target_blocks,
        "prepared_at": _now(),
    }
    receipt: dict[str, Any] = {
        "deliverable": code,
        "mode": mode,
        "output_path": output_path,
    }
    if mode == "no_op":
        state.setdefault("deliverables", {}).setdefault(code, {}).pop("pending", None)
        summary["status"] = "complete"
        _save_state(run_dir, state)
        return receipt
    receipt.update(
        {
            "author_path": author_path,
            "validation_path": author_path,
            "template_path": chosen,
            "dirty_entity_count": len(dirty_entities),
            "deleted_entity_count": len(deleted_entities),
            "target_blocks": target_blocks,
            "unmapped_entities": sorted(
                set(dirty_entities)
                - {
                    entity
                    for block in current_blocks.values()
                    for entity in block.get("entities") or []
                }
            ),
            "conflicts": conflicts,
        }
    )
    if not chosen:
        receipt["template_candidates"] = candidates
    if conflicts:
        raise KnowledgeError(f"manual edit conflict: {code}/" + ", ".join(conflicts))
    pending_document.parent.mkdir(parents=True, exist_ok=True)
    if mode in {"targeted", "marker_migration"}:
        shutil.copyfile(document, pending_document)
    state.setdefault("deliverables", {}).setdefault(code, {})["pending"] = pending
    summary["status"] = "generating"
    _save_state(run_dir, state)
    return receipt


def prepare_selected_generation(run_dir: Path) -> dict[str, Any]:
    """Prepare every selected deliverable through one compact CLI call."""
    state = _load_state(run_dir)
    selected = [str(code).upper() for code in state.get("selected_outputs") or []]
    if not selected:
        raise KnowledgeError("no deliverables are selected")
    return {
        "deliverables": [prepare_generation(run_dir, code, None) for code in selected],
    }


def document_blocks(
    run_dir: Path,
    deliverable: str,
    query: str | None = None,
) -> dict[str, Any]:
    """Return a compact ownership index for targeted document revision."""
    code = deliverable.upper()
    output = _output_config(code)
    output_path = str(output.get("outputPath") or "")
    if not output_path:
        raise KnowledgeError(f"workflow manifest outputPath is missing for {code}")
    document = _safe_run_path(run_dir, output_path)
    if not document.is_file():
        raise KnowledgeError(f"deliverable is missing: {output_path}")
    blocks, errors = _parse_blocks(_read_text(document))
    if errors:
        raise KnowledgeError("invalid render blocks: " + "; ".join(errors))
    terms = {token.lower() for token in re.findall(r"[A-Za-z0-9_-]{3,}", query or "")}
    rows: list[tuple[int, dict[str, Any]]] = []
    for block_id, block in blocks.items():
        heading = next(
            (
                line.lstrip("#").strip()
                for line in str(block.get("body") or "").splitlines()
                if line.lstrip().startswith("#")
            ),
            "",
        )
        entities = list(block.get("entities") or [])
        haystack = " ".join(
            [block_id, heading, *entities, str(block.get("body") or "")]
        ).lower()
        score = sum(haystack.count(term) for term in terms)
        if terms and not score:
            continue
        rows.append((score, {"id": block_id, "heading": heading, "entities": entities}))
    ordered = [
        row for _score, row in sorted(rows, key=lambda item: (-item[0], item[1]["id"]))
    ]
    return {"deliverable": code, "path": output_path, "blocks": ordered}


def generation_context(run_dir: Path, deliverable: str) -> dict[str, Any]:
    """Return the current transaction receipt without a persisted plan file."""
    code = deliverable.upper()
    state = _load_state(run_dir)
    output = _output_config(code)
    record = (state.get("deliverables") or {}).get(code) or {}
    pending = record.get("pending") or {}
    if not pending:
        raise KnowledgeError(f"{code} has no prepared generation transaction")
    entities = (state.get("knowledge") or {}).get("entities") or {}
    dirty = list(pending.get("dirty_entities") or [])
    output_path = str(output.get("outputPath"))
    routes = _generation_routes(run_dir, entities, dirty)
    authoring_batches = _generation_batches(run_dir, entities, dirty)
    for batch in authoring_batches:
        batch["command"] = (
            "python .claude/skills/requirements-agent/scripts/knowledge_layer.py "
            f"--run-dir . retrieve-context --deliverable {code} "
            f"--batch {batch['id']} --view authoring"
        )
    estimated_context = sum(
        int(batch.get("estimated_characters") or 0) for batch in authoring_batches
    )
    return {
        "deliverable": code,
        "mode": pending.get("mode"),
        "output_path": output_path,
        "author_path": pending.get("author_path"),
        "validation_path": pending.get("author_path"),
        "template_path": pending.get("template_path"),
        "routes": routes,
        "authoring_batches": authoring_batches,
        "write_strategy": "single",
        "estimated_context_characters": estimated_context,
        "dirty_entity_count": len(dirty),
        "deleted_entities": pending.get("deleted_entities") or [],
        "target_blocks": pending.get("target_blocks") or [],
        "authoring_contract": {
            "block_start": BLOCK_AUTHOR_START_TEMPLATE,
            "block_end": BLOCK_AUTHOR_END_TEMPLATE,
            "marker_rules": [
                "Use one unique semantic block ID in the matching START and END markers.",
                "List only applicable canonical knowledge IDs in entities; never list document-local IDs.",
                "Do not add attributes other than id and entities; commit adds the sha256 attribute.",
            ],
            "normative_rule": (
                "Each FRD or URS requirement ID has one independently verifiable "
                "obligation and one SHALL or SHALL NOT clause; acceptance criteria "
                "use observable non-normative language."
            ),
            "mechanical_rules": [
                "Never emit literal TBD, TODO, or placeholder text.",
                "Use only [INSUFFICIENT INPUT], [ASSUMPTION], or "
                "[INFERRED FROM DOMAIN KNOWLEDGE] for evidence gaps.",
                "Every evidence-gap marker has a corresponding Open Items row.",
                "Apply the normative rule during the first draft, before validation.",
            ],
        },
        "commands": {
            "validate": (
                "python .claude/skills/requirements-agent/scripts/"
                f"validate_requirements.py --file {pending.get('author_path')} --json"
            ),
            "check_generation": (
                "python .claude/skills/requirements-agent/scripts/knowledge_layer.py "
                f"--run-dir . check-generation --deliverable {code}"
            ),
        },
    }


def search_knowledge(
    run_dir: Path,
    query: str,
    deliverable: str | None,
    limit: int,
) -> dict[str, Any]:
    """Lexically seed relevant graph nodes without loading the Markdown corpus."""
    state = _load_state(run_dir)
    entities = (state.get("knowledge") or {}).get("entities") or {}
    sections = _entity_sections(run_dir)
    terms = {token.lower() for token in re.findall(r"[A-Za-z0-9_-]{3,}", query)}
    if not terms:
        raise KnowledgeError("search query has no meaningful terms")
    code = deliverable.upper() if deliverable else None
    scored = []
    for entity_id, item in entities.items():
        if code and code not in (item.get("deliverables") or []):
            continue
        haystack = (
            f"{entity_id} {item.get('title', '')} {sections.get(entity_id, '')}".lower()
        )
        score = sum(haystack.count(term) for term in terms)
        if entity_id.lower() in terms:
            score += 20
        if score:
            scored.append((score, entity_id, item))
    results = [
        {
            "id": entity_id,
            "title": item.get("title"),
            "path": f"{item.get('page')}#{item.get('anchor')}",
            "deliverables": item.get("deliverables") or [],
            "relations": item.get("relations") or [],
            "score": score,
        }
        for score, entity_id, item in sorted(scored, key=lambda row: (-row[0], row[1]))[
            :limit
        ]
    ]
    return {"query": query, "results": results}


def knowledge_routes(run_dir: Path, deliverable: str) -> dict[str, Any]:
    code = deliverable.upper()
    _output_config(code)
    state = _load_state(run_dir)
    entities = (state.get("knowledge") or {}).get("entities") or {}
    applicable = sorted(
        entity_id
        for entity_id, item in entities.items()
        if code in (item.get("deliverables") or [])
    )
    return {
        "deliverable": code,
        "entity_count": len(applicable),
        "routes": _generation_routes(run_dir, entities, applicable),
    }


def _retrieval_receipt(
    code: str,
    batch_id: str,
    batch_entities: list[str],
    pending: dict[str, Any],
    entities: dict[str, dict[str, Any]],
) -> str:
    """Create a stateless proof for one fresh-generation retrieval batch."""
    payload = {
        "deliverable": code,
        "batch": batch_id,
        "entities": batch_entities,
        "prepared_at": pending.get("prepared_at"),
        "entity_hashes": [
            str((entities.get(entity_id) or {}).get("content_sha256") or "")
            for entity_id in batch_entities
        ],
    }
    digest = _sha_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return (
        f'<!-- RA-RETRIEVAL-RECEIPT deliverable="{code}" '
        f'batch="{batch_id}" sha256="{digest}" -->'
    )


def retrieve_context(
    run_dir: Path,
    deliverable: str | None,
    route: str | None,
    requested_entities: list[str],
    query: str | None,
    max_entities: int,
    view: str = "authoring",
    batch: str | None = None,
) -> dict[str, Any]:
    """Retrieve exact entity sections plus a bounded one-hop graph neighborhood."""
    if view not in {"authoring", "full"}:
        raise KnowledgeError("retrieval view must be authoring or full")
    code = deliverable.upper() if deliverable else None
    state = _load_state(run_dir)
    pending = (
        (((state.get("deliverables") or {}).get(code) or {}).get("pending") or {})
        if code
        else {}
    )
    entities = (state.get("knowledge") or {}).get("entities") or {}
    if not code and not requested_entities:
        raise KnowledgeError(
            "retrieval without --deliverable requires at least one explicit --entity"
        )
    deleted = set(pending.get("deleted_entities") or [])
    if batch and (route or requested_entities or query):
        raise KnowledgeError("--batch cannot be combined with route, entity, or query")
    if batch and not pending:
        raise KnowledgeError(
            "batch retrieval requires a prepared deliverable transaction"
        )
    if pending and not route and not batch and not requested_entities:
        raise KnowledgeError(
            "generation retrieval requires --route or at least one explicit --entity"
        )
    if pending:
        authorized = [
            entity_id
            for entity_id in (pending.get("dirty_entities") or [])
            if entity_id in entities and entity_id not in deleted
        ]
    elif code:
        authorized = sorted(
            entity_id
            for entity_id, item in entities.items()
            if code in (item.get("deliverables") or [])
        )
    else:
        authorized = sorted(entities)
    seeds = authorized
    if batch:
        batches = {
            item["id"]: item
            for item in _generation_batches(run_dir, entities, authorized)
        }
        selected_batch = batches.get(batch)
        if not selected_batch:
            raise KnowledgeError(f"unknown authoring batch for {code}: {batch}")
        seeds = list(selected_batch["entities"])
    if route:
        normalized_route = route.replace("\\", "/")
        seeds = [
            entity_id
            for entity_id in seeds
            if str((entities.get(entity_id) or {}).get("page") or "")
            == normalized_route
        ]
    if requested_entities:
        requested = set(requested_entities)
        unknown = sorted(requested - set(authorized))
        if unknown:
            raise KnowledgeError(
                (
                    f"requested entities are outside the {code} transaction: "
                    if code
                    else "unknown knowledge entities: "
                )
                + ", ".join(unknown)
            )
        seeds = [entity_id for entity_id in seeds if entity_id in requested]

    sections = _entity_sections(run_dir)
    if query:
        terms = {token.lower() for token in re.findall(r"[A-Za-z0-9_-]{3,}", query)}
        scored = []
        for entity_id in seeds:
            haystack = f"{entity_id} {(entities.get(entity_id) or {}).get('title', '')} {sections.get(entity_id, '')}".lower()
            score = sum(haystack.count(term) for term in terms)
            if score:
                scored.append((score, entity_id))
        seeds = [entity_id for _score, entity_id in sorted(scored, reverse=True)]
    seeds = seeds[:max_entities]
    if not seeds:
        raise KnowledgeError("retrieval found no authorized entity sections")

    author_path = str(pending.get("author_path") or "")
    full_batch_prefetch = bool(
        pending and str(pending.get("mode") or "") == "full" and batch
    )
    retrieval_receipt = None
    if full_batch_prefetch:
        retrieval_receipt = _retrieval_receipt(
            str(code), str(batch), seeds, pending, entities
        )
    if pending and (route or batch or requested_entities) and not full_batch_prefetch:
        if not author_path:
            raise KnowledgeError(f"{code} pending document path is missing")
        author_document = _safe_run_path(run_dir, author_path)
        if not author_document.is_file() or author_document.stat().st_size == 0:
            raise KnowledgeError(
                f"write the {code} template skeleton to {author_path} before retrieving context"
            )
        authored = _read_text(author_document)
        prior_checkpoint = RETRIEVAL_CHECKPOINT_RE.search(authored)
        without_checkpoint = _strip_retrieval_checkpoint(authored)
        document_sha = _sha_text(without_checkpoint)
        if prior_checkpoint and prior_checkpoint.group("sha256") == document_sha:
            raise KnowledgeError(
                "the previously retrieved route has not been applied; update the pending "
                "document before retrieving another route"
            )
        checkpoint_scope = batch or route or ("entities:" + ",".join(seeds))
        previously_retrieved = (
            str(prior_checkpoint.group("entities") or "").split(",")
            if prior_checkpoint
            else []
        )
        retrieved = sorted(
            {
                entity_id.strip()
                for entity_id in [*previously_retrieved, *seeds]
                if entity_id.strip()
            }
        )
        checkpoint = (
            f'<!-- RA-RETRIEVAL-CHECKPOINT route="{checkpoint_scope.replace(chr(34), "")}" '
            f'entities="{",".join(retrieved)}" '
            f'sha256="{document_sha}" -->\n'
        )
        author_document.write_text(without_checkpoint + checkpoint, encoding="utf-8")

    neighbors = []
    seen = set(seeds)
    # A full render already traverses every applicable route, so expanding each
    # route with neighbor bodies would duplicate the same entities across calls.
    # Targeted work needs the bounded neighborhood for local relationship context.
    expand_neighbors = str(pending.get("mode") or "") != "full"
    if expand_neighbors:
        for entity_id in seeds:
            for target in _entity_neighbors(entities, entity_id):
                item = entities.get(target) or {}
                if (
                    target
                    and target not in seen
                    and target not in deleted
                    and (not code or code in (item.get("deliverables") or []))
                ):
                    seen.add(target)
                    neighbors.append(target)
                    if len(seen) >= max_entities:
                        break
            if len(seen) >= max_entities:
                break

    selected = [*seeds, *neighbors]
    rendered_sections = []
    for entity_id in selected:
        section = sections.get(entity_id)
        if not section:
            raise KnowledgeError(f"knowledge section is missing for {entity_id}")
        if view == "authoring":
            section = _authoring_entity_section(
                entity_id,
                section,
                entities.get(entity_id) or {},
            )
        else:
            section = re.sub(
                r"\[([^\]]*SRC-\d+[^\]]*)\]\((?:\.\./)*sources/[^)]+\)",
                r"\1",
                section,
            )
        rendered_sections.append(section)
    context = (
        "# Retrieved requirements context\n\n"
        + "\n\n---\n\n".join(rendered_sections)
        + "\n"
    )
    return {
        "deliverable": code,
        "view": view,
        "authoring_entities": seeds,
        "context_only_entities": neighbors,
        "insufficient_entities": [
            entity_id
            for entity_id in selected
            if (entities.get(entity_id) or {}).get("source_status") == "insufficient"
        ],
        "context_markdown": context,
        "context_characters": len(context),
        "retrieval_receipt": retrieval_receipt,
        "required_next_action": (
            "Preserve this retrieval_receipt exactly. Retrieve the next ordered batch; "
            f"after the final batch, write {author_path} once and append every receipt."
            if full_batch_prefetch
            else (
                f"Update {author_path} with the section supported by this retrieval before "
                "calling retrieve-context again."
                if pending and (route or batch or requested_entities)
                else None
            )
        ),
    }


def check_generation_coverage(run_dir: Path, deliverable: str) -> dict[str, Any]:
    """Validate ownership coverage without committing shared state."""
    code = deliverable.upper()
    state = _load_state(run_dir)
    pending = ((state.get("deliverables") or {}).get(code) or {}).get("pending") or {}
    mode = str(pending.get("mode") or "full")
    document_path = str(pending.get("author_path") or "")
    if not document_path:
        raise KnowledgeError(f"{code} pending document path is missing")
    document = _safe_run_path(run_dir, document_path)
    if not document.is_file() or document.stat().st_size == 0:
        raise KnowledgeError(f"deliverable is missing: {document_path}")
    raw_document = _read_text(document)
    retrieval_checkpoint = RETRIEVAL_CHECKPOINT_RE.search(raw_document)
    retrieved = {
        entity_id.strip()
        for entity_id in (
            str(retrieval_checkpoint.group("entities") or "").split(",")
            if retrieval_checkpoint
            else []
        )
        if entity_id.strip()
    }
    receipt_errors: list[str] = []
    if mode == "full":
        known = (state.get("knowledge") or {}).get("entities") or {}
        batches = {
            item["id"]: item
            for item in _generation_batches(
                run_dir,
                known,
                sorted(
                    set(pending.get("dirty_entities") or [])
                    - set(pending.get("deleted_entities") or [])
                ),
            )
        }
        seen_receipts: set[str] = set()
        for match in RETRIEVAL_RECEIPT_RE.finditer(raw_document):
            receipt_code = str(match.group("deliverable") or "")
            batch_id = str(match.group("batch") or "")
            if receipt_code != code:
                receipt_errors.append(
                    f"retrieval receipt for {receipt_code} is not valid in {code}"
                )
                continue
            if batch_id in seen_receipts:
                receipt_errors.append(f"duplicate retrieval receipt: {batch_id}")
                continue
            batch_row = batches.get(batch_id)
            if not batch_row:
                receipt_errors.append(f"unknown retrieval receipt batch: {batch_id}")
                continue
            expected = _retrieval_receipt(
                code,
                batch_id,
                list(batch_row["entities"]),
                pending,
                known,
            )
            expected_hash = str(RETRIEVAL_RECEIPT_RE.search(expected).group("sha256"))
            if match.group("sha256") != expected_hash:
                receipt_errors.append(f"stale or invalid retrieval receipt: {batch_id}")
                continue
            seen_receipts.add(batch_id)
            retrieved.update(batch_row["entities"])
    blocks, errors = _parse_blocks(_strip_retrieval_checkpoint(raw_document))
    if errors:
        raise KnowledgeError("invalid render blocks: " + "; ".join(errors))
    if not blocks:
        raise KnowledgeError(f"{code} has no RA-BLOCK ownership markers")
    dirty = set(pending.get("dirty_entities") or [])
    deleted = set(pending.get("deleted_entities") or [])
    covered = {
        entity for block in blocks.values() for entity in block.get("entities") or []
    }
    missing = sorted((dirty - deleted) - covered)
    known = (state.get("knowledge") or {}).get("entities") or {}
    applicable = {
        entity_id
        for entity_id, item in known.items()
        if code in (item.get("deliverables") or [])
    }
    unknown = sorted(covered - set(known)) if mode == "full" else []
    inapplicable = sorted((covered & set(known)) - applicable) if mode == "full" else []
    problems = list(receipt_errors)
    if "<!-- RA-TWO-PASS-CONTINUE -->" in raw_document:
        problems.append("two-pass authoring placeholder was not replaced")
    unretrieved = sorted((dirty - deleted) - retrieved)
    if mode != "marker_migration" and unretrieved:
        missing_batches = [
            item["id"]
            for item in _generation_batches(
                run_dir,
                known,
                sorted(dirty - deleted),
            )
            if set(item["entities"]) & set(unretrieved)
        ]
        problems.append(
            "required entities were marked as covered without retrieval evidence; "
            "retrieve missing batches: " + ", ".join(missing_batches)
        )
    if (
        mode != "full"
        and retrieval_checkpoint
        and retrieval_checkpoint.group("sha256")
        == _sha_text(_strip_retrieval_checkpoint(raw_document))
    ):
        problems.append(
            "the latest retrieved context has not been applied to the pending document; "
            "edit an authorized target block using that context, then rerun check-generation "
            "without inspecting or changing the retrieval checkpoint"
        )
    if missing:
        problems.append(f"missing required entities: {', '.join(missing)}")
    if unknown:
        problems.append(
            "ownership markers contain document-local or unknown IDs; keep those IDs in prose only: "
            + ", ".join(unknown)
        )
    if inapplicable:
        problems.append(
            f"ownership markers contain entities not applicable to {code}: "
            + ", ".join(inapplicable)
        )
    if problems:
        raise KnowledgeError(
            f"{code} coverage check failed:\n- " + "\n- ".join(problems)
        )
    return {
        "deliverable": code,
        "mode": mode,
        "validated_path": document_path,
        "blocks": len(blocks),
        "required_entities": len(dirty - deleted),
        "retrieved_entities": len(retrieved),
        "covered_entities": len(covered),
        "status": "valid",
    }


def _validate_generation_transaction(
    run_dir: Path, deliverable: str, template: str | None = None
) -> dict[str, Any]:
    """Validate a prepared document without changing its public artifact or state."""
    code = deliverable.upper()
    state = _load_state(run_dir)
    output = _output_config(code)
    document_path = str(output.get("outputPath"))
    document = _safe_run_path(run_dir, document_path)
    record = state.setdefault("deliverables", {}).setdefault(code, {})
    pending = record.get("pending") or {}
    if not pending:
        raise KnowledgeError(f"{code} has no prepared generation transaction")
    mode = str(pending.get("mode") or "full")
    authored_path = str(pending.get("author_path") or "")
    if not authored_path:
        raise KnowledgeError(f"{code} pending document path is missing")
    authored_document = _safe_run_path(run_dir, authored_path)
    if not authored_document.is_file() or authored_document.stat().st_size == 0:
        raise KnowledgeError(f"deliverable is missing: {authored_path}")
    text = _strip_retrieval_checkpoint(_read_text(authored_document)).lstrip("\ufeff")
    blocks, errors = _parse_blocks(text)
    if errors:
        raise KnowledgeError("invalid render blocks: " + "; ".join(errors))
    if not blocks:
        raise KnowledgeError(f"{code} has no RA-BLOCK ownership markers")

    check_generation_coverage(run_dir, code)
    allowed_target_blocks = set(pending.get("target_blocks") or [])
    baseline_hash = pending.get("baseline_document_sha256")
    baseline_text = _read_text(document) if document.is_file() else ""
    if baseline_hash and _sha_text(baseline_text) != baseline_hash:
        raise KnowledgeError(
            f"manual edit conflict: {code} public document changed after prepare"
        )
    if mode == "targeted":
        if _outside_blocks_signature(
            baseline_text, allowed_target_blocks
        ) != _outside_blocks_signature(text, allowed_target_blocks):
            raise KnowledgeError(
                "targeted update changed content outside blocks owned by dirty entities"
            )
    if mode == "marker_migration":
        baseline = pending.get("baseline_without_markers_sha256")
        if baseline and _sha_text(_strip_markers(text)) != baseline:
            raise KnowledgeError("marker migration changed document prose")

    template_path = (
        template or pending.get("template_path") or record.get("template_path")
    )
    if not template_path:
        raise KnowledgeError(f"template path is required when committing {code}")
    resolved_template = _safe_template_path(run_dir, template_path)
    if not resolved_template.is_file():
        raise KnowledgeError(f"template does not exist: {template_path}")

    return {
        "code": code,
        "state": state,
        "record": record,
        "pending": pending,
        "mode": mode,
        "document_path": document_path,
        "document": document,
        "authored_path": authored_path,
        "authored_document": authored_document,
        "text": text,
        "blocks": blocks,
        "template_path": template_path,
        "resolved_template": resolved_template,
    }


def commit_generation(
    run_dir: Path, deliverable: str, template: str | None
) -> dict[str, Any]:
    validated = _validate_generation_transaction(run_dir, deliverable, template)
    code = validated["code"]
    state = validated["state"]
    record = validated["record"]
    mode = validated["mode"]
    document_path = validated["document_path"]
    document = validated["document"]
    authored_document = validated["authored_document"]
    text = validated["text"]
    blocks = validated["blocks"]
    template_path = validated["template_path"]
    resolved_template = validated["resolved_template"]

    normalized = _normalize_block_markers(text)
    temporary = authored_document.with_suffix(authored_document.suffix + ".tmp")
    temporary.write_text(normalized, encoding="utf-8")
    _replace_with_retry(temporary, authored_document)
    blocks, _errors = _parse_blocks(normalized)
    covered_entities = {
        entity for block in blocks.values() for entity in block.get("entities") or []
    }
    document.parent.mkdir(parents=True, exist_ok=True)
    _replace_with_retry(authored_document, document)

    record.update(
        {
            "path": document_path,
            "template_path": template_path,
            "template_sha256": _sha_file(resolved_template),
            "document_sha256": _sha_file(document),
            "completed_at": _now(),
        }
    )
    record.pop("blocks", None)
    record.pop("pending", None)
    summary = state.setdefault("generation_summary", {}).setdefault(code, {})
    summary.update(
        {
            "status": "complete",
            "dirty_entities": [],
            "block_count": len(blocks),
            "completed_at": _now(),
        }
    )
    state["phases"]["evaluate"] = {"status": "dirty"}
    state["evaluation"] = {"status": "dirty"}
    _save_state(run_dir, state)
    return {
        "deliverable": code,
        "mode": mode,
        "path": document_path,
        "blocks": len(blocks),
        "entities": len(covered_entities),
    }


def finalize_selected_generation(run_dir: Path) -> dict[str, Any]:
    """Prevalidate every pending selected document, then commit them serially."""
    validator_path = Path(__file__).with_name("validate_requirements.py")
    validator_spec = importlib.util.spec_from_file_location(
        "requirements_validate_requirements", validator_path
    )
    if validator_spec is None or validator_spec.loader is None:
        raise KnowledgeError(
            f"could not load deterministic validator: {validator_path}"
        )
    validator = importlib.util.module_from_spec(validator_spec)
    validator_spec.loader.exec_module(validator)
    state = _load_state(run_dir)
    selected = [str(code).upper() for code in state.get("selected_outputs") or []]
    prepared: list[tuple[str, str | None, dict[str, Any]]] = []
    for code in selected:
        record = (state.get("deliverables") or {}).get(code) or {}
        pending = record.get("pending") or {}
        if not pending:
            continue
        author_path = str(pending.get("author_path") or "")
        if not author_path:
            raise KnowledgeError(f"{code} pending document path is missing")
        authored_document = _safe_run_path(run_dir, author_path)
        findings = validator.lint_file(authored_document)
        errors = [item for item in findings if item.get("severity") == "error"]
        if errors:
            details = "; ".join(
                f"{item.get('rule')} line {item.get('line')}: {item.get('message')}"
                for item in errors
            )
            raise KnowledgeError(f"{code} deterministic validation failed: {details}")
        _validate_generation_transaction(
            run_dir,
            code,
            pending.get("template_path") or record.get("template_path"),
        )
        prepared.append(
            (
                code,
                pending.get("template_path") or record.get("template_path"),
                validator._summary(findings),
            )
        )

    committed = []
    for code, template_path, lint_summary in prepared:
        receipt = commit_generation(run_dir, code, template_path)
        receipt["lint"] = lint_summary
        committed.append(receipt)
    return {"committed": committed, "count": len(committed)}


def _snapshot_hash(run_dir: Path, paths: list[Path]) -> str:
    """Hash a named file set so an evaluation cannot outlive its evidence."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: _relative(run_dir, item)):
        relative = _relative(run_dir, path)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _evaluation_snapshot(run_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    source_rows = []
    source_paths: list[Path] = []
    for source_path, record in sorted((state.get("sources") or {}).items()):
        if not isinstance(record, dict) or record.get("current_sha256") is None:
            continue
        source_id = str(record.get("source_id") or "")
        if not source_id:
            raise KnowledgeError(f"source has no stable ID: {source_path}")
        read_path = str(record.get("text_path") or record.get("path") or "")
        if not read_path:
            raise KnowledgeError(f"{source_id} has no readable evidence path")
        path = _safe_run_path(run_dir, read_path)
        if not path.is_file():
            raise KnowledgeError(f"{source_id} evidence is missing: {read_path}")
        evidence_sha256 = _sha_file(path)
        source_paths.append(path)
        source_rows.append(
            {
                "source_id": source_id,
                "read_path": read_path,
                "evidence_sha256": evidence_sha256,
                "source_role": (
                    "semantic_evidence" if record.get("semantic") else "control_input"
                ),
            }
        )

    knowledge_paths = _all_knowledge_pages(run_dir)
    if not knowledge_paths:
        raise KnowledgeError("knowledge layer is empty")

    deliverable_rows = []
    deliverable_paths: list[Path] = []
    for code in state.get("selected_outputs") or []:
        record = (state.get("deliverables") or {}).get(code) or {}
        output_path = str(record.get("output_path") or "")
        if not output_path:
            raise KnowledgeError(f"deliverable state output_path is missing for {code}")
        path = _safe_run_path(run_dir, output_path)
        if (
            record.get("status") != "complete"
            or not path.is_file()
            or path.stat().st_size == 0
        ):
            raise KnowledgeError(f"selected deliverable is not complete: {code}")
        deliverable_paths.append(path)
        deliverable_rows.append(
            {"deliverable": code, "path": output_path, "sha256": _sha_file(path)}
        )

    return {
        "sources_sha256": _snapshot_hash(run_dir, source_paths),
        "knowledge_sha256": _snapshot_hash(run_dir, knowledge_paths),
        "deliverables_sha256": _snapshot_hash(run_dir, deliverable_paths),
        "sources": source_rows,
        "deliverables": deliverable_rows,
    }


def prepare_evaluation(run_dir: Path) -> dict[str, Any]:
    """Open one evaluation transaction against an immutable content snapshot."""
    state = _load_state(run_dir)
    snapshot = _evaluation_snapshot(run_dir, state)
    aggregate_snapshot = {
        key: snapshot[key]
        for key in ("sources_sha256", "knowledge_sha256", "deliverables_sha256")
    }
    current = state.get("evaluation") or {}
    if (
        current.get("status") == "in_progress"
        and current.get("evaluation_id")
        and current.get("snapshot") == aggregate_snapshot
    ):
        return {
            "evaluation_id": current["evaluation_id"],
            "prepared_at": current.get("prepared_at"),
            "selected_outputs": list(state.get("selected_outputs") or []),
            "snapshot": snapshot,
            "pending_outputs": {
                name: (EVALUATION_PENDING_PATH / name).as_posix()
                for name in EVALUATION_FILENAMES
            },
            "reused_transaction": True,
        }
    prepared_at = _now()
    evaluation_id = (
        "EVAL-"
        + _sha_text(
            "\n".join(
                [
                    prepared_at,
                    snapshot["sources_sha256"],
                    snapshot["knowledge_sha256"],
                    snapshot["deliverables_sha256"],
                ]
            )
        )[:16].upper()
    )
    pending_dir = _safe_run_path(run_dir, EVALUATION_PENDING_PATH)
    if pending_dir.exists():
        shutil.rmtree(pending_dir)
    pending_dir.mkdir(parents=True, exist_ok=True)
    state["phases"]["evaluate"] = {"status": "in_progress", "started_at": prepared_at}
    state["evaluation"] = {
        "status": "in_progress",
        "evaluation_id": evaluation_id,
        "prepared_at": prepared_at,
        "snapshot": {
            **aggregate_snapshot,
        },
    }
    _save_state(run_dir, state)
    return {
        "evaluation_id": evaluation_id,
        "prepared_at": prepared_at,
        "selected_outputs": list(state.get("selected_outputs") or []),
        "snapshot": snapshot,
        "pending_outputs": {
            name: (EVALUATION_PENDING_PATH / name).as_posix()
            for name in EVALUATION_FILENAMES
        },
    }


def evaluation_context(run_dir: Path) -> dict[str, Any]:
    """Return the live immutable evaluation receipt without mutating it."""
    state = _load_state(run_dir)
    current = state.get("evaluation") or {}
    if current.get("status") != "in_progress" or not current.get("evaluation_id"):
        raise KnowledgeError(
            "no prepared evaluation transaction; the parent must run prepare-evaluation"
        )
    snapshot = _evaluation_snapshot(run_dir, state)
    aggregate = {
        key: snapshot[key]
        for key in ("sources_sha256", "knowledge_sha256", "deliverables_sha256")
    }
    if aggregate != current.get("snapshot"):
        raise KnowledgeError(
            "prepared evaluation snapshot is stale; the parent must prepare again"
        )
    artifact_metadata = {
        "evaluation_report.md": {
            "evaluation_id": current["evaluation_id"],
            "snapshot": aggregate,
        },
        "quality_scores.json": {
            "meta": {
                "evaluation_id": current["evaluation_id"],
                "snapshot": aggregate,
            }
        },
        "traceability.yaml": {
            "meta": {
                "evaluation_id": current["evaluation_id"],
                "snapshot": aggregate,
            }
        },
    }
    source_coverage_seed = [
        {
            "source_id": source["source_id"],
            "source_sha256": source["evidence_sha256"],
            "source_role": source["source_role"],
            "read_path": source["read_path"],
        }
        for source in snapshot["sources"]
    ]
    return {
        "evaluation_id": current["evaluation_id"],
        "prepared_at": current.get("prepared_at"),
        "selected_outputs": list(state.get("selected_outputs") or []),
        "snapshot": snapshot,
        "artifact_metadata": artifact_metadata,
        "source_coverage_seed": source_coverage_seed,
        "pending_outputs": {
            name: (EVALUATION_PENDING_PATH / name).as_posix()
            for name in EVALUATION_FILENAMES
        },
    }


def invalidate_evaluation(run_dir: Path, reason: str) -> dict[str, Any]:
    """Invalidate an evaluation after an externally edited public artifact."""
    clean_reason = reason.strip()
    if not clean_reason:
        raise KnowledgeError("evaluation invalidation requires a reason")
    state = _load_state(run_dir)
    pending_dir = _safe_run_path(run_dir, EVALUATION_PENDING_PATH)
    if pending_dir.exists():
        shutil.rmtree(pending_dir)
    state["phases"]["evaluate"] = {"status": "dirty"}
    state["evaluation"] = {
        "status": "dirty",
        "invalidated_at": _now(),
        "reason": clean_reason,
    }
    _save_state(run_dir, state)
    return {"status": "dirty", "reason": clean_reason}


def _evaluation_metadata(payload: Any, artifact: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise KnowledgeError(f"{artifact} must contain a mapping")
    meta = payload.get("meta") if artifact != "evaluation_report.md" else payload
    if not isinstance(meta, dict):
        raise KnowledgeError(f"{artifact} meta must be a mapping")
    return meta


def _validate_evaluation_bundle(
    run_dir: Path,
    state: dict[str, Any],
    pending_paths: dict[str, Path],
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        scores = json.loads(_read_text(pending_paths["quality_scores.json"]))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeError("pending quality_scores.json is invalid") from exc
    try:
        traceability = yaml.safe_load(_read_text(pending_paths["traceability.yaml"]))
    except (OSError, yaml.YAMLError) as exc:
        raise KnowledgeError("pending traceability.yaml is invalid") from exc
    try:
        report_meta, report_body = _frontmatter(
            _read_text(pending_paths["evaluation_report.md"])
        )
    except (OSError, KnowledgeError) as exc:
        raise KnowledgeError(f"pending evaluation_report.md is invalid: {exc}") from exc
    if not report_body.strip():
        raise KnowledgeError("pending evaluation_report.md has no report body")

    expected = state.get("evaluation") or {}
    evaluation_id = expected.get("evaluation_id")
    snapshot = expected.get("snapshot") or {}
    for name, payload in (
        ("evaluation_report.md", report_meta),
        ("quality_scores.json", scores),
        ("traceability.yaml", traceability),
    ):
        meta = _evaluation_metadata(payload, name)
        if meta.get("evaluation_id") != evaluation_id:
            raise KnowledgeError(
                f"{name} belongs to a different evaluation transaction"
            )
        artifact_snapshot = meta.get("snapshot")
        if artifact_snapshot != snapshot:
            raise KnowledgeError(
                f"{name} snapshot does not match the prepared evaluation"
            )

    current_snapshot = _evaluation_snapshot(run_dir, state)
    for field in ("sources_sha256", "knowledge_sha256", "deliverables_sha256"):
        if current_snapshot[field] != snapshot.get(field):
            raise KnowledgeError(f"evaluation snapshot is stale: {field} changed")

    if not isinstance(scores, dict):
        raise KnowledgeError("quality_scores.json must be an object")
    for section in ("knowledge_evaluation", "output_evaluation"):
        value = scores.get(section)
        if not isinstance(value, dict):
            raise KnowledgeError(f"quality_scores.json is missing {section}")
        section_score = value.get("score")
        if (
            not isinstance(section_score, (int, float))
            or isinstance(section_score, bool)
            or not 0 <= section_score <= 100
        ):
            raise KnowledgeError(f"{section}.score must be between 0 and 100")
        if not isinstance(value.get("gate"), str) or not value["gate"].strip():
            raise KnowledgeError(f"{section}.gate is required")
        defects = value.get("defects")
        if not isinstance(defects, list):
            raise KnowledgeError(f"{section}.defects must be a list")
        expected_domain = "knowledge" if section == "knowledge_evaluation" else "output"
        if any(
            not isinstance(item, dict) or item.get("domain") != expected_domain
            for item in defects
        ):
            raise KnowledgeError(
                f"{section} defects must use domain: {expected_domain}"
            )
        actionable_severities = {"critical", "error", "major", "minor", "warning"}
        if any(
            str(item.get("severity") or "").lower() not in actionable_severities
            for item in defects
        ):
            raise KnowledgeError(
                f"{section}.defects contains a non-actionable severity; "
                "put informational observations in observations"
            )
        for item in defects:
            for field in ("finding", "impact", "remediation"):
                if not str(item.get(field) or "").strip():
                    raise KnowledgeError(f"{section}.defects needs {field}")
            impact = str(item.get("impact") or "").strip().lower().rstrip(".")
            remediation = str(item.get("remediation") or "").strip().lower().rstrip(".")
            if impact in {"none", "n/a", "not applicable"} or remediation in {
                "none",
                "n/a",
                "not applicable",
                "no action required",
                "no remediation required",
            }:
                raise KnowledgeError(
                    f"{section}.defects contains a no-action observation; "
                    "move it to observations"
                )
        observations = value.get("observations", [])
        if not isinstance(observations, list):
            raise KnowledgeError(f"{section}.observations must be a list when present")

    verdict = scores.get("verdict")
    if not isinstance(verdict, dict):
        raise KnowledgeError("quality_scores.json is missing verdict")
    score = verdict.get("overall_score")
    gate = verdict.get("gate") or verdict.get("quality_gate")
    if (
        not isinstance(score, (int, float))
        or isinstance(score, bool)
        or not 0 <= score <= 100
    ):
        raise KnowledgeError("verdict.overall_score must be between 0 and 100")
    if not isinstance(gate, str) or not gate.strip():
        raise KnowledgeError("verdict.gate is required")
    report_verdict = {
        "overall_score": report_meta.get("overall_score"),
        "gate": report_meta.get("gate"),
        "knowledge_score": report_meta.get("knowledge_score"),
        "output_score": report_meta.get("output_score"),
    }
    expected_report_verdict = {
        "overall_score": score,
        "gate": gate,
        "knowledge_score": scores["knowledge_evaluation"]["score"],
        "output_score": scores["output_evaluation"]["score"],
    }
    if report_verdict != expected_report_verdict:
        raise KnowledgeError(
            "evaluation report scores do not match quality_scores.json"
        )

    if not isinstance(traceability, dict):
        raise KnowledgeError("traceability.yaml must contain a mapping")
    coverage = traceability.get("source_coverage")
    if not isinstance(coverage, list):
        raise KnowledgeError("traceability.yaml is missing source_coverage")
    actual_sources = {row["source_id"]: row for row in current_snapshot["sources"]}
    reviewed_sources: dict[str, dict[str, Any]] = {}
    allowed_statuses = {
        "covered",
        "context_only",
        "duplicate",
        "superseded",
        "out_of_scope",
        "unresolved",
    }
    for row in coverage:
        if not isinstance(row, dict) or not row.get("source_id"):
            raise KnowledgeError("every source_coverage row needs source_id")
        source_id = str(row["source_id"])
        if source_id in reviewed_sources:
            raise KnowledgeError(f"duplicate source_coverage row: {source_id}")
        if source_id not in actual_sources:
            raise KnowledgeError(f"source_coverage names unknown source: {source_id}")
        # These fields are immutable transaction metadata, not reviewer
        # judgments. Normalize them from the prepared snapshot so the model
        # cannot fabricate or stale-copy a hash/path while preserving every
        # independently authored coverage judgment below.
        source = actual_sources[source_id]
        row["source_sha256"] = source["evidence_sha256"]
        row["source_role"] = source["source_role"]
        row["read_path"] = source["read_path"]
        if row.get("status") not in allowed_statuses:
            raise KnowledgeError(f"source_coverage has invalid status: {source_id}")
        if row.get("evidence_checked") is not True:
            raise KnowledgeError(
                f"source_coverage was not independently checked: {source_id}"
            )
        if not isinstance(row.get("knowledge_concepts"), list):
            raise KnowledgeError(
                f"source_coverage needs knowledge_concepts: {source_id}"
            )
        if row.get("status") == "covered" and not row["knowledge_concepts"]:
            raise KnowledgeError(
                f"covered source has no knowledge concepts: {source_id}"
            )
        if not str(row.get("disposition") or "").strip():
            raise KnowledgeError(f"source_coverage needs a disposition: {source_id}")
        reviewed_sources[source_id] = row
    missing_sources = sorted(set(actual_sources) - set(reviewed_sources))
    if missing_sources:
        raise KnowledgeError(
            "source_coverage omits sources: " + ", ".join(missing_sources)
        )
    return scores, traceability


def commit_evaluation(run_dir: Path) -> dict[str, Any]:
    state = _load_state(run_dir)
    pending_paths = {
        name: _safe_run_path(run_dir, EVALUATION_PENDING_PATH / name)
        for name in EVALUATION_FILENAMES
    }
    missing = [name for name, path in pending_paths.items() if not path.is_file()]
    if missing:
        current = state.get("evaluation") or {}
        if current.get("status") == "complete" and len(missing) == len(
            EVALUATION_FILENAMES
        ):
            return {
                "evaluation_id": current.get("evaluation_id"),
                "overall_score": current.get("overall_score"),
                "quality_gate": current.get("quality_gate"),
                "status": "complete",
                "already_committed": True,
            }
        raise KnowledgeError(
            "pending evaluation outputs are missing: " + ", ".join(missing)
        )
    if (state.get("evaluation") or {}).get("status") != "in_progress":
        raise KnowledgeError("prepare-evaluation must run before commit-evaluation")
    # Validation failure must not destroy the prepared snapshot identity. The
    # caller can repair a malformed pending artifact and retry the same atomic
    # transaction. A truly changed source/knowledge/output snapshot will keep
    # failing with an explicit stale-snapshot error until prepare is invoked
    # intentionally again.
    scores, traceability = _validate_evaluation_bundle(run_dir, state, pending_paths)
    _write_if_changed(
        pending_paths["traceability.yaml"],
        yaml.safe_dump(traceability, allow_unicode=True, sort_keys=False),
    )

    output_dir = _safe_run_path(run_dir, EVALUATION_PATH)
    output_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = _safe_run_path(run_dir, EVALUATION_PATH / ".previous")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(parents=True)
    moved_existing: list[str] = []
    published: list[str] = []
    try:
        for name in EVALUATION_FILENAMES:
            target = output_dir / name
            if target.exists():
                _replace_with_retry(target, backup_dir / name)
                moved_existing.append(name)
        for name in EVALUATION_FILENAMES:
            _replace_with_retry(pending_paths[name], output_dir / name)
            published.append(name)
    except OSError:
        for name in published:
            target = output_dir / name
            if target.exists():
                target.unlink()
        for name in moved_existing:
            backup = backup_dir / name
            if backup.exists():
                _replace_with_retry(backup, output_dir / name)
        raise
    finally:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        pending_dir = _safe_run_path(run_dir, EVALUATION_PENDING_PATH)
        if pending_dir.exists() and not any(pending_dir.iterdir()):
            pending_dir.rmdir()

    verdict = scores["verdict"]
    completed_at = _now()
    state["phases"]["evaluate"] = {"status": "complete", "completed_at": completed_at}
    state["evaluation"] = {
        "status": "complete",
        "evaluation_id": (scores.get("meta") or {}).get("evaluation_id"),
        "overall_score": verdict["overall_score"],
        "quality_gate": verdict.get("gate") or verdict.get("quality_gate"),
        "completed_at": completed_at,
    }
    _save_state(run_dir, state)
    return state["evaluation"]


def commit_publication(run_dir: Path) -> dict[str, Any]:
    mapping_path = "outputs/04_publish_handoff/jira_issue_mapping.json"
    summary_path = "outputs/04_publish_handoff/jira_publish_summary.md"
    mapping_file = _safe_run_path(run_dir, mapping_path)
    summary_file = _safe_run_path(run_dir, summary_path)
    if not mapping_file.is_file() or not summary_file.is_file():
        raise KnowledgeError("Jira publication mapping and summary are required")
    try:
        mapping = json.loads(_read_text(mapping_file))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeError("jira_issue_mapping.json is invalid") from exc
    state = _load_state(run_dir)
    state["publication"] = {
        "status": "published",
        "issue_count": len(mapping.get("issues") or [])
        if isinstance(mapping, dict)
        else 0,
        "completed_at": _now(),
    }
    _save_state(run_dir, state)
    return state["publication"]


def status(run_dir: Path) -> dict[str, Any]:
    state = _load_state(run_dir)
    source_statuses = [
        str(value.get("status") or "unknown")
        for value in (state.get("sources") or {}).values()
        if isinstance(value, dict)
    ]
    summaries = {}
    for code, raw in (state.get("generation_summary") or {}).items():
        item = raw if isinstance(raw, dict) else {}
        summaries[code] = {
            key: value
            for key, value in {
                "status": item.get("status"),
                "dirty_entity_count": len(item.get("dirty_entities") or []),
                "block_count": item.get("block_count"),
                "completed_at": item.get("completed_at"),
            }.items()
            if value is not None
        }
    knowledge = state.get("knowledge") or {}
    return {
        "schema_version": state.get("schema_version"),
        "selected_outputs": state.get("selected_outputs") or [],
        "phases": state.get("phases") or {},
        "sources": {
            status: source_statuses.count(status)
            for status in sorted(set(source_statuses))
        },
        "knowledge": {
            "pages": len(knowledge.get("page_hashes") or {}),
            "entities": len(knowledge.get("entity_hashes") or {}),
            "changed_entity_count": len(knowledge.get("changed_entities") or []),
        },
        "generation_summary": summaries,
        "evaluation": state.get("evaluation") or {},
    }


def _print(payload: Any) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("initialize")
    sub.add_parser("refresh-inputs")
    sub.add_parser("plan-start")
    overview = sub.add_parser("source-overview")
    overview.add_argument("--phase", choices=("start", "extract"), required=True)
    overview.add_argument("--all", action="store_true")
    start = sub.add_parser("commit-start")
    start.add_argument("--selected", action="append", required=True)
    sub.add_parser("plan-extract")
    sub.add_parser("commit-extract")
    validate = sub.add_parser("validate")
    validate.add_argument("--links-only", action="store_true")
    sub.add_parser("normalize-links")
    backlinks = sub.add_parser("backlinks")
    backlinks.add_argument("--path", required=True)
    prepare = sub.add_parser("prepare-generation")
    prepare_target = prepare.add_mutually_exclusive_group(required=True)
    prepare_target.add_argument("--deliverable")
    prepare_target.add_argument("--selected", action="store_true")
    prepare.add_argument("--template")
    prepare.add_argument("--block", action="append", default=[])
    prepare.add_argument("--entity", action="append", default=[])
    block_index = sub.add_parser("document-blocks")
    block_index.add_argument("--deliverable", required=True)
    block_index.add_argument("--query")
    context = sub.add_parser("generation-context")
    context.add_argument("--deliverable", required=True)
    search = sub.add_parser("search-knowledge")
    search.add_argument("--query", required=True)
    search.add_argument("--deliverable")
    search.add_argument("--limit", type=int, default=12)
    routes = sub.add_parser("knowledge-routes")
    routes.add_argument("--deliverable", required=True)
    retrieve = sub.add_parser("retrieve-context")
    retrieve.add_argument("--deliverable")
    retrieve.add_argument("--route")
    retrieve.add_argument("--batch")
    retrieve.add_argument("--entity", action="append", default=[])
    retrieve.add_argument(
        "--entities",
        help="Comma-separated alias for repeated --entity arguments",
    )
    retrieve.add_argument("--query")
    retrieve.add_argument("--max-entities", type=int, default=40)
    retrieve.add_argument("--view", choices=("authoring", "full"), default="authoring")
    coverage = sub.add_parser("check-generation")
    coverage.add_argument("--deliverable", required=True)
    commit = sub.add_parser("commit-generation")
    commit.add_argument("--deliverable", required=True)
    commit.add_argument("--template")
    sub.add_parser("finalize-generation")
    sub.add_parser("prepare-evaluation")
    sub.add_parser("evaluation-context")
    invalidate = sub.add_parser("invalidate-evaluation")
    invalidate.add_argument("--reason", required=True)
    sub.add_parser("commit-evaluation")
    sub.add_parser("commit-publication")
    sub.add_parser("status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    try:
        if args.command == "initialize":
            _ensure_layout(run_dir)
            path = _save_state(run_dir, _load_state(run_dir))
            _print(
                {
                    "state_path": _relative(run_dir, path),
                    "knowledge_path": KNOWLEDGE_PATH.as_posix(),
                }
            )
        elif args.command in {"refresh-inputs", "plan-start"}:
            _print(refresh_inputs(run_dir))
        elif args.command == "source-overview":
            _print(source_overview(run_dir, args.phase, args.all))
        elif args.command == "commit-start":
            _print(commit_start(run_dir, args.selected))
        elif args.command == "plan-extract":
            _print(plan_extract(run_dir))
        elif args.command == "commit-extract":
            _print(commit_extract(run_dir))
        elif args.command == "validate":
            entities: dict[str, dict[str, Any]] = {}
            errors = [
                *_validate_okf_bundle(run_dir),
                *validate_links(run_dir),
            ]
            if not args.links_only:
                entities, entity_errors = _parse_entities(run_dir)
                errors.extend(entity_errors)
                coverage_errors, _coverage, _coverage_rows = _validate_source_coverage(
                    run_dir, entities
                )
                errors.extend(coverage_errors)
            if errors:
                raise KnowledgeError("validation failed:\n- " + "\n- ".join(errors))
            _print(
                {
                    "status": "valid",
                    "pages": len(_all_knowledge_pages(run_dir)),
                    "entities": len(entities),
                }
            )
        elif args.command == "normalize-links":
            _print(normalize_entity_links(run_dir))
        elif args.command == "backlinks":
            _print({"path": args.path, "backlinks": _backlinks(run_dir, args.path)})
        elif args.command == "prepare-generation":
            if args.selected:
                if args.template or args.block or args.entity:
                    raise KnowledgeError(
                        "--template, --block, and --entity require --deliverable"
                    )
                _print(prepare_selected_generation(run_dir))
            else:
                _print(
                    prepare_generation(
                        run_dir,
                        args.deliverable,
                        args.template,
                        args.block,
                        args.entity,
                    )
                )
        elif args.command == "document-blocks":
            _print(document_blocks(run_dir, args.deliverable, args.query))
        elif args.command == "generation-context":
            _print(generation_context(run_dir, args.deliverable))
        elif args.command == "search-knowledge":
            if args.limit < 1 or args.limit > 100:
                raise KnowledgeError("--limit must be between 1 and 100")
            _print(search_knowledge(run_dir, args.query, args.deliverable, args.limit))
        elif args.command == "knowledge-routes":
            _print(knowledge_routes(run_dir, args.deliverable))
        elif args.command == "retrieve-context":
            if args.max_entities < 1 or args.max_entities > 200:
                raise KnowledgeError("--max-entities must be between 1 and 200")
            entity_ids = list(args.entity)
            if args.entities:
                entity_ids.extend(
                    entity_id.strip()
                    for entity_id in args.entities.split(",")
                    if entity_id.strip()
                )
            _print(
                retrieve_context(
                    run_dir,
                    args.deliverable,
                    args.route,
                    entity_ids,
                    args.query,
                    args.max_entities,
                    args.view,
                    args.batch,
                )
            )
        elif args.command == "check-generation":
            _print(check_generation_coverage(run_dir, args.deliverable))
        elif args.command == "commit-generation":
            _print(commit_generation(run_dir, args.deliverable, args.template))
        elif args.command == "finalize-generation":
            _print(finalize_selected_generation(run_dir))
        elif args.command == "prepare-evaluation":
            _print(prepare_evaluation(run_dir))
        elif args.command == "evaluation-context":
            _print(evaluation_context(run_dir))
        elif args.command == "invalidate-evaluation":
            _print(invalidate_evaluation(run_dir, args.reason))
        elif args.command == "commit-evaluation":
            _print(commit_evaluation(run_dir))
        elif args.command == "commit-publication":
            _print(commit_publication(run_dir))
        elif args.command == "status":
            _print(status(run_dir))
        return 0
    except (KnowledgeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
