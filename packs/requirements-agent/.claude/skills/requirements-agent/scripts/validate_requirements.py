#!/usr/bin/env python3
"""Fast deterministic lint for final requirements Markdown.

Semantic grounding, traceability, and readiness belong to the quality reviewer
and the linked knowledge validator. This script catches only mechanical defects
that are cheaper and more reliable to detect with text rules.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


VALID_MARKERS = (
    "[INSUFFICIENT INPUT]",
    "[ASSUMPTION]",
    "[INFERRED FROM DOMAIN KNOWLEDGE]",
)
RA_BLOCK_MARKER_RE = re.compile(
    r'^\s*<!--\s*RA-BLOCK\s+(?:START\s+id="[^"]+"(?:\s+entities="[^"]*")?'
    r'(?:\s+sha256="[0-9a-f]{64}")?|END\s+id="[^"]+")\s*-->\s*$'
)
RA_RETRIEVAL_CHECKPOINT_RE = re.compile(
    r'^\s*<!--\s*RA-RETRIEVAL-CHECKPOINT\s+route="[^"]+"\s+'
    r'(?:entities="[^"]*"\s+)?sha256="[0-9a-f]{64}"\s*-->\s*$'
)
RA_RETRIEVAL_RECEIPT_RE = re.compile(
    r'^\s*<!--\s*RA-RETRIEVAL-RECEIPT\s+deliverable="[A-Z0-9_-]+"\s+'
    r'batch="[A-Za-z0-9_.:-]+"\s+sha256="[a-f0-9]{64}"\s*-->\s*$'
)
RESIDUE_PATTERNS = (
    (re.compile(r"<!--"), "leaked HTML template comment"),
    (re.compile(r"<[A-Z][A-Z0-9_]{2,}>"), "unresolved uppercase placeholder"),
    (re.compile(r"<[A-Z][a-z]+ [A-Z][a-z]+>"), "unresolved named placeholder"),
    (re.compile(r"\[(?:PLACEHOLDER|TBD|TODO)\]", re.IGNORECASE), "placeholder marker"),
    (re.compile(r"\b(?:TODO|TBD)\b"), "TODO/TBD left in deliverable"),
)
AMBIGUITY_TERMS = (
    "robust", "scalable", "seamless", "intuitive", "user-friendly",
    "user friendly", "flexible", "fast", "quickly", "promptly",
    "near real-time", "timely", "several", "many", "sufficient",
    "appropriate", "adequate", "minimal", "as needed", "where possible",
    "better", "improved", "optimized", "high quality",
)
AMBIGUITY_RE = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in AMBIGUITY_TERMS) + r")\b",
    re.IGNORECASE,
)
SHALL_RE = re.compile(r"\bshall\b", re.IGNORECASE)
OPEN_ITEMS_RE = re.compile(r"^#{1,6}\s+.*open items", re.IGNORECASE | re.MULTILINE)
TABLE_SEPARATOR_CANDIDATE_RE = re.compile(r"^\s*\|.*-{3,}.*\|.*$")
VALID_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")


def _finding(
    filename: str,
    line: int,
    rule: str,
    severity: str,
    message: str,
    evidence: str = "",
) -> dict[str, Any]:
    return {
        "file": filename,
        "line": line,
        "rule": rule,
        "severity": severity,
        "message": message,
        "evidence": evidence[:200],
    }


def _strip_inline_code(line: str) -> str:
    return re.sub(r"`[^`]*`", "", line)


def lint_text(text: str, filename: str = "<text>") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    marker_seen = False
    in_code_fence = False

    for line_number, raw in enumerate(text.splitlines(), start=1):
        if raw.lstrip().startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if (
            in_code_fence
            or RA_BLOCK_MARKER_RE.fullmatch(raw)
            or RA_RETRIEVAL_CHECKPOINT_RE.fullmatch(raw)
            or RA_RETRIEVAL_RECEIPT_RE.fullmatch(raw)
        ):
            continue

        line = _strip_inline_code(raw)
        if any(marker in raw for marker in VALID_MARKERS):
            marker_seen = True

        if TABLE_SEPARATOR_CANDIDATE_RE.match(raw) and not VALID_TABLE_SEPARATOR_RE.match(raw):
            findings.append(
                _finding(filename, line_number, "R6", "error", "malformed Markdown table separator", raw.strip())
            )

        scrubbed = line
        for marker in VALID_MARKERS:
            scrubbed = scrubbed.replace(marker, "")
        for pattern, message in RESIDUE_PATTERNS:
            if pattern.search(scrubbed):
                findings.append(_finding(filename, line_number, "R1", "error", message, raw.strip()))

        shall_count = len(SHALL_RE.findall(line))
        if shall_count > 1:
            findings.append(
                _finding(
                    filename,
                    line_number,
                    "R4",
                    "error",
                    "compound requirement: split multiple shall clauses into atomic requirements",
                    raw.strip(),
                )
            )
        if shall_count:
            for term in sorted({match.lower() for match in AMBIGUITY_RE.findall(line)}):
                findings.append(
                    _finding(
                        filename,
                        line_number,
                        "R3",
                        "warn",
                        f"vague term '{term}' in a formal requirement; quantify it or add an Open Item",
                        raw.strip(),
                    )
                )

    if marker_seen and not OPEN_ITEMS_RE.search(text):
        findings.append(
            _finding(
                filename,
                0,
                "R2",
                "error",
                "document carries evidence-gap markers but has no Open Items section",
            )
        )
    return findings


def lint_file(path: Path) -> list[dict[str, Any]]:
    try:
        return lint_text(path.read_text(encoding="utf-8"), str(path))
    except OSError as exc:
        return [_finding(str(path), 0, "IO", "error", f"could not read file: {exc}")]


def _summary(findings: list[dict[str, Any]]) -> dict[str, Any]:
    by_severity: dict[str, int] = {}
    by_rule: dict[str, int] = {}
    for finding in findings:
        severity = str(finding["severity"])
        rule = str(finding["rule"])
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_rule[rule] = by_rule.get(rule, 0) + 1
    return {"total": len(findings), "by_severity": by_severity, "by_rule": by_rule}


def _selftest() -> int:
    bad = (
        "# Requirements\n"
        "The system shall be fast and user-friendly.\n"
        "The platform shall validate and the service shall load.\n"
        "Replace <EPIC_KEY>.\n"
        "<!-- leaked note -->\n"
        "[ASSUMPTION] SCD Type 2.\n"
    )
    good = (
        "# Requirements\n"
        '<!-- RA-BLOCK START id="scope" entities="FR-001" '
        'sha256="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" -->\n'
        "The system shall finish validation within five minutes.\n"
        '<!-- RA-BLOCK END id="scope" -->\n'
        "The `<EPIC_KEY>` token is filled at publication.\n"
        "[ASSUMPTION] SCD Type 2.\n"
        "## Open Items\n\n- Confirm the assumption.\n"
    )
    bad_rules = {finding["rule"] for finding in lint_text(bad, "bad.md")}
    good_errors = [
        finding for finding in lint_text(good, "good.md") if finding["severity"] == "error"
    ]
    ok = {"R1", "R2", "R3", "R4"}.issubset(bad_rules) and not good_errors
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*")
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--run-dir")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    targets = [Path(value) for value in [*args.files, *args.file]]
    if args.run_dir:
        targets.extend(sorted(Path(args.run_dir).glob("outputs/02_deliverables/*.md")))
    if not targets:
        parser.error("provide files, --run-dir, or --selftest")

    findings = [finding for target in targets for finding in lint_file(target)]
    summary = _summary(findings)
    if args.json:
        print(json.dumps({"findings": findings, "summary": summary}, indent=2))
    elif not findings:
        print("OK - no deterministic lint findings.")
    else:
        for finding in findings:
            location = f"{finding['file']}:{finding['line']}" if finding["line"] else finding["file"]
            print(f"[{finding['severity'].upper()}] {finding['rule']} {location} - {finding['message']}")
        print(f"\n{summary['total']} finding(s): {summary['by_severity']}")
    has_error = any(finding["severity"] == "error" for finding in findings)
    return 1 if args.strict and has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
