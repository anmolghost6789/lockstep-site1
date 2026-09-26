#!/usr/bin/env python3
"""Append-only, hash-chained ADLC audit log.

  append  --event gate.requested --phase discover-define [--gate G1] [--data '{"k": "v"}']
  verify  exits 1 if any entry was modified, removed or reordered
  export  --format jsonl|csv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys

from _common import identity, now, repo_root

GENESIS = "0" * 64


def _digest(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _read(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append(event: str, phase: str | None = None, gate: str | None = None, data: dict | None = None, actor: str | None = None) -> dict:
    root = repo_root()
    path = root / "adlc/.audit/audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = _read(path)
    prev = entries[-1]["hash"] if entries else GENESIS
    entry = {
        "seq": len(entries) + 1,
        "ts": now(),
        "event": event,
        "phase": phase,
        "gate": gate,
        "actor": actor or _safe_identity(),
        "data": data or {},
        "prev_hash": prev,
    }
    entry["hash"] = _digest(entry)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def _safe_identity() -> str:
    try:
        return identity()
    except SystemExit:
        return "agent"


def verify() -> int:
    path = repo_root() / "adlc/.audit/audit.jsonl"
    prev = GENESIS
    for i, entry in enumerate(_read(path), start=1):
        if entry.get("seq") != i or entry.get("prev_hash") != prev or _digest(entry) != entry.get("hash"):
            print(f"AUDIT CHAIN BROKEN at entry {i} (seq={entry.get('seq')}).")
            return 1
        prev = entry["hash"]
    print(f"Audit chain intact: {len(_read(path))} entries.")
    return 0


def export(fmt: str) -> int:
    entries = _read(repo_root() / "adlc/.audit/audit.jsonl")
    if fmt == "jsonl":
        for e in entries:
            print(json.dumps(e, ensure_ascii=False))
        return 0
    w = csv.writer(sys.stdout)
    w.writerow(["seq", "ts", "event", "phase", "gate", "actor", "data", "hash"])
    for e in entries:
        w.writerow([e["seq"], e["ts"], e["event"], e["phase"], e["gate"], e["actor"], json.dumps(e["data"]), e["hash"]])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("append")
    a.add_argument("--event", required=True)
    a.add_argument("--phase")
    a.add_argument("--gate")
    a.add_argument("--data", default="{}")
    sub.add_parser("verify")
    e = sub.add_parser("export")
    e.add_argument("--format", choices=["jsonl", "csv"], default="jsonl")
    args = ap.parse_args()
    if args.cmd == "append":
        entry = append(args.event, args.phase, args.gate, json.loads(args.data))
        print(f"audit #{entry['seq']} {entry['event']}")
        return 0
    if args.cmd == "verify":
        return verify()
    return export(args.format)


if __name__ == "__main__":
    sys.exit(main())
