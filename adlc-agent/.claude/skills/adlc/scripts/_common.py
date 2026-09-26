"""Shared helpers for ADLC scripts and hooks. Standard library only."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import subprocess
from pathlib import Path

IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))


def repo_root(start: Path | None = None) -> Path:
    """Walk up from start (or cwd) to the folder that holds CLAUDE.md and .claude/."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and (Path(env) / "CLAUDE.md").exists():
        return Path(env).resolve()
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "CLAUDE.md").exists() and (candidate / ".claude").is_dir():
            return candidate
    raise SystemExit("ADLC: could not find the package root (a folder with CLAUDE.md and .claude/).")


def now() -> str:
    return _dt.datetime.now(IST).isoformat(timespec="seconds")


def parse_ts(value: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(value)


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(root: Path) -> dict:
    return load_json(root / ".claude/skills/adlc/workflow_manifest.json")


def phase_by_id(root: Path, phase_id: str) -> dict:
    for p in manifest(root)["phases"]:
        if p["id"] == phase_id:
            return p
    raise SystemExit(f"ADLC: unknown phase '{phase_id}'.")


def phase_by_gate(root: Path, gate_id: str) -> dict:
    for p in manifest(root)["phases"]:
        if p["gate"] == gate_id:
            return p
    raise SystemExit(f"ADLC: unknown gate '{gate_id}'.")


def identity() -> str:
    """Approver identity. The VS Code extension sets ADLC_IDENTITY from the SSO token."""
    ident = os.environ.get("ADLC_IDENTITY", "").strip()
    if ident:
        return ident.lower()
    try:
        out = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, timeout=5)
        if out.stdout.strip():
            return out.stdout.strip().lower()
    except (OSError, subprocess.SubprocessError):
        pass
    raise SystemExit("ADLC: no identity. Sign in through the extension (sets ADLC_IDENTITY) or set git user.email.")


def roles_for(root: Path, ident: str) -> set[str]:
    """Roles come from IdP groups (ADLC_GROUPS) when present, otherwise from static members."""
    cfg = load_json(root / "config/governance/gate_roles.json")
    groups_env = os.environ.get(cfg["identity"].get("groups_env", "ADLC_GROUPS"), "")
    roles: set[str] = set()
    if groups_env.strip():
        for g in [g.strip() for g in groups_env.split(",") if g.strip()]:
            role = cfg["group_role_map"].get(g)
            if role:
                roles.add(role)
        return roles
    for role, members in cfg.get("static_members", {}).items():
        if ident in [m.lower() for m in members]:
            roles.add(role)
    return roles
