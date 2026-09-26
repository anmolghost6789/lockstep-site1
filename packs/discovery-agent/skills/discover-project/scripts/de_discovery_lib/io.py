"""Safe local I/O and runtime path resolution."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class DiscoveryError(RuntimeError):
    """Expected user-facing discovery failure."""


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DiscoveryError(f"File not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise DiscoveryError(f"Invalid YAML in {path}: {exc}") from exc
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DiscoveryError(f"Expected a YAML mapping in {path}")
    return value


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_write_yaml(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(
        path,
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=1000),
    )


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def ensure_within(path: Path, parent: Path, label: str) -> Path:
    resolved = path.resolve()
    root = parent.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise DiscoveryError(f"{label} must stay within project root: {resolved}") from exc
    return resolved


@dataclass(frozen=True)
class RuntimePaths:
    project_root: Path
    config_path: Path
    runtime_root: Path
    state_path: Path
    evidence_root: Path
    reports_root: Path
    knowledge_root: Path

    @classmethod
    def resolve(
        cls,
        project_root: str | Path,
        config_name: str | Path = ".de-discovery.yaml",
        *,
        require_config: bool = True,
    ) -> "RuntimePaths":
        root = Path(project_root).expanduser().resolve()
        if not root.is_dir():
            raise DiscoveryError(f"Project root is not a directory: {root}")

        candidate = Path(config_name)
        config_path = candidate if candidate.is_absolute() else root / candidate
        config_path = ensure_within(config_path, root, "Configuration")

        if require_config:
            config = load_yaml(config_path)
            knowledge_value = config.get("knowledge_root", "knowledge")
        else:
            config = load_yaml(config_path) if config_path.exists() else {}
            knowledge_value = config.get("knowledge_root", "knowledge")

        if not isinstance(knowledge_value, str) or not knowledge_value.strip():
            raise DiscoveryError("knowledge_root must be a non-empty relative path")
        knowledge_candidate = Path(knowledge_value)
        if knowledge_candidate.is_absolute():
            raise DiscoveryError("knowledge_root must be relative to the project root")
        if knowledge_candidate in {Path("."), Path("")}:
            raise DiscoveryError("knowledge_root cannot be the project root")
        if knowledge_candidate.parts[0].casefold() in {".de-discovery", ".git"}:
            raise DiscoveryError("knowledge_root cannot overlap runtime or Git metadata")

        knowledge_root = ensure_within(root / knowledge_candidate, root, "Knowledge root")
        runtime_root = ensure_within(root / ".de-discovery", root, "Runtime root")
        return cls(
            project_root=root,
            config_path=config_path,
            runtime_root=runtime_root,
            state_path=runtime_root / "state.yaml",
            evidence_root=runtime_root / "evidence",
            reports_root=runtime_root / "reports",
            knowledge_root=knowledge_root,
        )
