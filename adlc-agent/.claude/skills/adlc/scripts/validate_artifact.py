#!/usr/bin/env python3
"""Validate a phase artifact against its contract.

  validate_artifact.py --phase discover-define

Checks: required sections or keys, no unfilled template placeholders, IDs use the
phase's prefixes, and every `Trace:` / `trace:` reference resolves to an ID defined
in an upstream artifact. Writes adlc/.state/validation/<phase>.json. Exit 1 on errors.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from _common import manifest, now, phase_by_id, repo_root, write_json

ID_RE = r"\b({prefixes})-\d{{3}}\b"
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}|\bTBD\b|\bTODO\b")
TRACE_RE = re.compile(r"(?i)\btrace\s*:\s*\[?([A-Z0-9 ,\-]+)\]?")


def _headings(text: str) -> set[str]:
    return {m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", text, re.M)}


def validate(phase_id: str) -> dict:
    root = repo_root()
    phases = manifest(root)["phases"]
    phase = phase_by_id(root, phase_id)
    path = root / phase["artifact"]
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return {"phase": phase_id, "artifact": phase["artifact"], "passed": False, "errors": ["artifact missing"], "warnings": []}
    text = path.read_text(encoding="utf-8")

    if path.suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON: {exc}")
            data = {}
        for key in phase.get("requiredKeys", []):
            if key not in data:
                errors.append(f"missing key: {key}")
        for m in data.get("metrics", []):
            for field in ("id", "name", "threshold", "value", "passed", "trace"):
                if field not in m:
                    errors.append(f"metric {m.get('id', '?')} missing '{field}'")
            if m.get("trace") == []:
                errors.append(f"metric {m.get('id')} has an empty trace; every metric must trace to an NFR or SC")
        if data.get("metrics"):
            all_pass = all(m.get("passed") for m in data["metrics"])
            if data.get("verdict") == "pass" and not all_pass:
                errors.append("verdict is 'pass' but at least one metric failed")
    elif path.suffix in (".yaml", ".yml"):
        for key in phase.get("requiredKeys", []):
            if not re.search(rf"^{re.escape(key)}\s*:", text, re.M):
                errors.append(f"missing key: {key}")
    else:
        present = _headings(text)
        for section in phase.get("requiredSections", []):
            if section not in present:
                errors.append(f"missing section: ## {section}")

    for m in PLACEHOLDER_RE.finditer(text):
        errors.append(f"unfilled placeholder: {m.group(0)}")
        if len(errors) > 25:
            break

    own = {m.group(0) for m in re.finditer(ID_RE.format(prefixes="|".join(phase["idPrefixes"])), text)}
    if not own:
        errors.append(f"no IDs found with prefixes {phase['idPrefixes']}")

    # Upstream IDs available for tracing.
    upstream: set[str] = set()
    for p in phases:
        if p["id"] == phase_id:
            break
        up = root / p["artifact"]
        if up.exists():
            up_text = up.read_text(encoding="utf-8")
            upstream |= {m.group(0) for m in re.finditer(ID_RE.format(prefixes="|".join(p["idPrefixes"])), up_text)}
    known = upstream | own
    refs: set[str] = set()
    for m in TRACE_RE.finditer(text):
        refs |= {t.strip() for t in m.group(1).split(",") if re.fullmatch(r"[A-Z]+-\d{3}", t.strip())}
    json_refs = re.findall(r'"trace"\s*:\s*\[([^\]]*)\]', text)
    for chunk in json_refs:
        refs |= set(re.findall(r"[A-Z]+-\d{3}", chunk))
    dangling = sorted(refs - known)
    for ref in dangling:
        errors.append(f"trace reference {ref} does not exist upstream")
    if phase_id != "discover-define" and not refs:
        errors.append("no trace references to upstream artifacts")

    result = {
        "phase": phase_id,
        "artifact": phase["artifact"],
        "checked_at": now(),
        "passed": not errors,
        "ids_defined": len(own),
        "trace_refs": len(refs),
        "errors": errors,
        "warnings": warnings,
    }
    write_json(root / "adlc/.state/validation" / f"{phase_id}.json", result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", required=True)
    args = ap.parse_args()
    result = validate(args.phase)
    status = "PASS" if result["passed"] else "FAIL"
    print(f"{status} {result['artifact']}: {result.get('ids_defined', 0)} IDs, {result.get('trace_refs', 0)} trace refs, {len(result['errors'])} errors")
    for e in result["errors"][:20]:
        print(f"  - {e}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
