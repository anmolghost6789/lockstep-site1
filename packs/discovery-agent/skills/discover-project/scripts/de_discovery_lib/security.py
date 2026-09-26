"""Conservative secret detection that never echoes captured values."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretFinding:
    line: int
    detector: str


_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("databricks_pat", re.compile(r"\bdapi[a-fA-F0-9]{24,}\b")),
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    (
        "assigned_secret",
        re.compile(
            r"(?i)(?:^|[\s,{])(?:[a-z0-9]+[_-])?"
            r"(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
            r"\s*[:=]\s*[\"']?(?!\$\{|\{\{|<|REDACTED|CHANGEME|replace-me)"
            r"[A-Za-z0-9_./+=:@-]{12,}"
        ),
    ),
)


def scan_text(text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for name, pattern in _PATTERNS:
            if pattern.search(line):
                findings.append(SecretFinding(line=line_number, detector=name))
    return findings
