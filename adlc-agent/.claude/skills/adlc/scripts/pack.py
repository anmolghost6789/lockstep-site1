#!/usr/bin/env python3
"""Lockstep pack manager: install, upgrade and roll back packs from a Lockstep registry.

  pack.py list     --registry URL --token T              approved packs in the registry
  pack.py install  --registry URL --token T --pack adlc [--version 1.2.0] [--dir .]
  pack.py upgrade  --registry URL --token T [--version 1.3.0]
  pack.py rollback                                         undo the last install or upgrade
  pack.py status                                           installed pack, version, local changes
  pack.py verify                                           which pack files were edited locally

Safety rules:
  - Every download is checked against the registry's sha256 before anything is written.
  - Files you edited are never overwritten: the new version is written next to them as
    <file>.upstream-<version> and listed as a conflict for you to merge.
  - Project-owned paths (config/, context/, memory/, inputs/, adlc/, .claude/settings.json)
    are only ever created, never replaced.
  - Every install and upgrade takes a backup under .lockstep/backups/, so rollback is exact.
Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

STATE = ".lockstep"
PROJECT_OWNED = ("config/", "context/", "memory/", "inputs/", "adlc/", ".claude/settings.json")


def digest(files: list[dict]) -> str:
    """Same algorithm as the registry, so a pack's sha256 can be checked locally."""
    h = hashlib.sha256()
    for f in sorted(files, key=lambda x: x["path"]):
        for part in (f["path"], f.get("encoding") or "utf8", f["content"]):
            h.update(part.encode("utf-8"))
            h.update(b"\0")
    return h.hexdigest()


def body(f: dict) -> bytes:
    return base64.b64decode(f["content"]) if f.get("encoding") == "base64" else f["content"].encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(registry: str, token: str, path: str) -> dict:
    req = urllib.request.Request(registry.rstrip("/") + path, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Registry error {e.code}: {e.read().decode()[:200]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Could not reach the registry: {e.reason}")


def get_pack(registry, token, name, version=None) -> dict:
    q = f"?version={urllib.parse.quote(version)}" if version else ""
    pack = fetch(registry, token, f"/api/registry/skills/{urllib.parse.quote(name)}{q}")
    if digest(pack["files"]) != pack["sha256"]:
        raise SystemExit("Checksum mismatch: the download does not match the registry's sha256. Nothing was written.")
    return pack


def load_installed(root: Path) -> dict | None:
    p = root / STATE / "installed.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save_installed(root: Path, data: dict) -> None:
    (root / STATE).mkdir(exist_ok=True)
    (root / STATE / "installed.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def owned(path: str) -> bool:
    return path.startswith(PROJECT_OWNED)


def apply(root: Path, pack: dict, registry: str, previous: dict | None) -> dict:
    """Write a pack version, protecting local edits. Returns a report."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = root / STATE / "backups" / f"{pack['name']}-{(previous or {}).get('version', 'none')}-to-{pack['version']}-{stamp}"
    backup.mkdir(parents=True)
    report = {"written": [], "added": [], "kept_local": [], "conflicts": [], "removed": [], "unchanged": 0}
    old_files = (previous or {}).get("files", {})
    new_paths = set()
    recorded: dict[str, str] = {}

    def back_up(rel: str):
        src = root / rel
        if src.exists():
            dst = backup / "files" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    for f in pack["files"]:
        rel = f["path"]
        new_paths.add(rel)
        data = body(f)
        new_sha = sha(data)
        target = root / rel
        if target.exists():
            local_sha = sha(target.read_bytes())
            if local_sha == new_sha:
                report["unchanged"] += 1
                recorded[rel] = new_sha
                continue
            edited = rel not in old_files or local_sha != old_files[rel]
            if owned(rel) or edited:
                side = target.with_name(f"{target.name}.upstream-{pack['version']}")
                side.write_bytes(data)
                report["conflicts" if edited and not owned(rel) else "kept_local"].append(rel)
                recorded[rel] = local_sha if not edited else old_files.get(rel, local_sha)
                continue
            back_up(rel)
            target.write_bytes(data)
            report["written"].append(rel)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            report["added"].append(rel)
        recorded[rel] = new_sha

    for rel, old_sha in old_files.items():
        if rel in new_paths or owned(rel):
            continue
        target = root / rel
        if target.exists() and sha(target.read_bytes()) == old_sha:
            back_up(rel)
            target.unlink()
            report["removed"].append(rel)
        elif target.exists():
            report["conflicts"].append(f"{rel} (removed upstream, edited locally; kept)")

    if previous:
        (backup / "installed.json").write_text(json.dumps(previous, indent=2), encoding="utf-8")
    (backup / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    save_installed(root, {
        "name": pack["name"], "version": pack["version"], "sha256": pack["sha256"], "registry": registry,
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "files": recorded, "backup": str(backup.relative_to(root)),
    })
    return report


def print_report(r: dict, pack: dict) -> None:
    print(f"{pack['name']} {pack['version']}: {len(r['added'])} added, {len(r['written'])} updated, {len(r['removed'])} removed, {r['unchanged']} unchanged")
    for rel in r["kept_local"]:
        print(f"  kept yours: {rel}  (new version saved as {Path(rel).name}.upstream-{pack['version']})")
    for rel in r["conflicts"]:
        print(f"  CONFLICT:   {rel}  (you edited this file; merge the .upstream-{pack['version']} copy)")


def cmd_list(a) -> int:
    for s in fetch(a.registry, a.token, "/api/registry/skills")["skills"]:
        print(f"{s['name']:<22} {s['version']:<9} {s.get('kind', 'skill'):<6} {s['files']:>4} files  {s['description'][:70]}")
    return 0


def cmd_install(a) -> int:
    root = Path(a.dir).resolve()
    if load_installed(root) and not a.force:
        print("A pack is already installed here. Use `upgrade`, or `install --force` to reinstall.")
        return 2
    pack = get_pack(a.registry, a.token, a.pack, a.version)
    print_report(apply(root, pack, a.registry, load_installed(root) if a.force else None), pack)
    return 0


def cmd_upgrade(a) -> int:
    root = Path(a.dir).resolve()
    cur = load_installed(root)
    if not cur:
        print("Nothing installed. Use `install` first.")
        return 2
    pack = get_pack(a.registry or cur["registry"], a.token, cur["name"], a.version)
    if pack["sha256"] == cur["sha256"]:
        print(f"{cur['name']} {cur['version']} is already the requested version.")
        return 0
    r = apply(root, pack, a.registry or cur["registry"], cur)
    print(f"Upgraded from {cur['version']}.")
    print_report(r, pack)
    notes = [f for f in pack["files"] if f["path"] in (f"migrations/{pack['version']}.md", "CHANGELOG.md")]
    for n in notes:
        print(f"\n--- {n['path']} ---\n{body(n).decode('utf-8', 'replace')[:1500]}")
    return 1 if r["conflicts"] else 0


def cmd_rollback(a) -> int:
    root = Path(a.dir).resolve()
    cur = load_installed(root)
    if not cur or not cur.get("backup"):
        print("Nothing to roll back.")
        return 2
    backup = root / cur["backup"]
    report = json.loads((backup / "report.json").read_text(encoding="utf-8"))
    for rel in report["added"]:
        p = root / rel
        if p.exists() and sha(p.read_bytes()) == cur["files"].get(rel):
            p.unlink()
    files_dir = backup / "files"
    if files_dir.exists():
        for src in files_dir.rglob("*"):
            if src.is_file():
                dst = root / src.relative_to(files_dir)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    prev = backup / "installed.json"
    if prev.exists():
        shutil.copy2(prev, root / STATE / "installed.json")
        print(f"Rolled back {cur['name']} {cur['version']} to {json.loads(prev.read_text())['version']}.")
    else:
        (root / STATE / "installed.json").unlink()
        print(f"Removed {cur['name']} {cur['version']}; there was no earlier version.")
    return 0


def cmd_status(a) -> int:
    root = Path(a.dir).resolve()
    cur = load_installed(root)
    if not cur:
        print("No pack installed.")
        return 0
    edited = [rel for rel, h in cur["files"].items() if (root / rel).exists() and sha((root / rel).read_bytes()) != h]
    missing = [rel for rel in cur["files"] if not (root / rel).exists()]
    print(f"{cur['name']} {cur['version']} from {cur['registry']}, installed {cur['installed_at']}")
    print(f"{len(cur['files'])} files; {len(edited)} edited locally; {len(missing)} missing")
    return 0


def cmd_verify(a) -> int:
    root = Path(a.dir).resolve()
    cur = load_installed(root)
    if not cur:
        print("No pack installed.")
        return 2
    bad = 0
    for rel, h in sorted(cur["files"].items()):
        p = root / rel
        if not p.exists():
            print(f"missing   {rel}"); bad += 1
        elif sha(p.read_bytes()) != h:
            print(f"edited    {rel}"); bad += 1
    print("All pack files match the installed version." if not bad else f"{bad} file(s) differ from {cur['name']} {cur['version']}.")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("list", "install", "upgrade"):
        p = sub.add_parser(name)
        p.add_argument("--registry", required=name != "upgrade")
        p.add_argument("--token", required=True)
        p.add_argument("--dir", default=".")
        if name == "install":
            p.add_argument("--pack", required=True)
            p.add_argument("--force", action="store_true")
        if name in ("install", "upgrade"):
            p.add_argument("--version")
    for name in ("rollback", "status", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--dir", default=".")
    a = ap.parse_args()
    return {"list": cmd_list, "install": cmd_install, "upgrade": cmd_upgrade, "rollback": cmd_rollback, "status": cmd_status, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
