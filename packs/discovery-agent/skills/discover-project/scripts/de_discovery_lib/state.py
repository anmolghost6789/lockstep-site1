"""Resumable local state with source revision and resource registries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .io import DiscoveryError, atomic_write_yaml, load_yaml, utc_now
from .security import scan_text


PHASES = {
    "intake",
    "clarify",
    "plan",
    "discover",
    "synthesize",
    "validate",
    "complete",
    "blocked",
}


def initial_state(project_id: str) -> dict[str, Any]:
    return {
        "version": "1",
        "project_id": project_id,
        "phase": "intake",
        "last_completed_step": None,
        "updated_at": utc_now(),
        "open_questions": [],
        "sources": {},
        "pending_source_revisions": [],
        "source_reviews": [],
        "created_resources": [],
    }


def load_state(path: Path, project_id: str) -> dict[str, Any]:
    if not path.exists():
        return initial_state(project_id)
    state = load_yaml(path)
    if str(state.get("version")) != "1":
        raise DiscoveryError("Unsupported state version")
    if state.get("project_id") != project_id:
        raise DiscoveryError(
            f"State project_id {state.get('project_id')!r} does not match config {project_id!r}"
        )
    state.setdefault("open_questions", [])
    state.setdefault("sources", {})
    state.setdefault("pending_source_revisions", [])
    state.setdefault("source_reviews", [])
    state.setdefault("created_resources", [])
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    serialized = yaml.safe_dump(state, sort_keys=False, allow_unicode=True, width=1000)
    findings = scan_text(serialized)
    if findings:
        locations = ", ".join(
            f"line {item.line} ({item.detector})" for item in findings[:10]
        )
        raise DiscoveryError(f"Potential secret detected in local state; refused at {locations}")
    atomic_write_yaml(path, state)


def set_phase(path: Path, state: dict[str, Any], phase: str, last_step: str | None) -> None:
    if phase not in PHASES:
        raise DiscoveryError(f"Unknown phase {phase!r}; expected one of {sorted(PHASES)}")
    state["phase"] = phase
    if last_step is not None:
        state["last_completed_step"] = last_step
    save_state(path, state)


def all_source_revision_ids(state: dict[str, Any]) -> set[str]:
    return {
        revision["id"]
        for source in state.get("sources", {}).values()
        for revision in source.get("revisions", [])
        if isinstance(revision, dict) and isinstance(revision.get("id"), str)
    }


def record_resource(
    path: Path,
    state: dict[str, Any],
    *,
    resource_type: str,
    name: str,
    resource_uri: str | None,
    purpose: str,
) -> dict[str, Any]:
    if resource_uri and "://" in resource_uri:
        from urllib.parse import urlsplit

        parsed = urlsplit(resource_uri)
        if parsed.username or parsed.password:
            raise DiscoveryError("Resource URI must not contain embedded credentials")
    existing = next(
        (
            item
            for item in state["created_resources"]
            if item.get("type") == resource_type and item.get("name") == name
        ),
        None,
    )
    if existing:
        return existing
    item = {
        "type": resource_type,
        "name": name,
        "resource_uri": resource_uri,
        "purpose": purpose,
        "recorded_at": utc_now(),
    }
    state["created_resources"].append(item)
    save_state(path, state)
    return item


def review_source(
    path: Path,
    state: dict[str, Any],
    *,
    revision_id: str,
    disposition: str,
    concepts: list[str],
    reason: str,
) -> dict[str, Any]:
    allowed = {"applied", "reviewed-no-change", "out-of-scope"}
    if disposition not in allowed:
        raise DiscoveryError(f"disposition must be one of {sorted(allowed)}")
    pending = next(
        (
            item
            for item in state["pending_source_revisions"]
            if item.get("revision_id") == revision_id
        ),
        None,
    )
    if not pending:
        raise DiscoveryError(f"Source revision is not pending review: {revision_id}")
    if disposition == "applied" and not concepts:
        raise DiscoveryError("Applied source revisions require at least one canonical concept ID")
    review = {
        **pending,
        "disposition": disposition,
        "concepts": concepts,
        "reason": reason,
        "reviewed_at": utc_now(),
    }
    state["pending_source_revisions"] = [
        item
        for item in state["pending_source_revisions"]
        if item.get("revision_id") != revision_id
    ]
    state["source_reviews"].append(review)
    save_state(path, state)
    return review
