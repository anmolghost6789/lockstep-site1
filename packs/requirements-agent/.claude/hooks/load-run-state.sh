#!/usr/bin/env bash
# Hook: load-run-state
# Event: SessionStart
# Purpose: Print safe root progress + memory context for standalone Claude Code sessions.

set -euo pipefail

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PROGRESS_FILE="$PROJECT_ROOT/progress.json"

echo "## Requirements Agent - Session Context"
echo ""

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    PYTHON_BIN=""
fi

if [ -f "$PROGRESS_FILE" ] && [ -n "$PYTHON_BIN" ]; then
    "$PYTHON_BIN" - "$PROGRESS_FILE" <<'PY' 2>/dev/null || echo "- (progress.json parse failed)"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
run_label = path.parent.name
current = data.get("current_step") or data.get("current_phase") or "not set"
selected = data.get("selected_outputs") or []
steps = data.get("steps") or []
done = [str(step.get("id")) for step in steps if step.get("status") == "done" and step.get("id")]
next_step = data.get("next") or {}
next_label = next_step.get("command") or next_step.get("label") or next_step.get("id") or "not set"

print(f"### Active run: {run_label}")
print(f"- Current step: {current}")
if selected:
    print(f"- Selected outputs: {', '.join(str(item) for item in selected)}")
if done:
    print(f"- Done: {', '.join(done)}")
print(f"- Next: {next_label}")
PY
    echo ""
else
    echo "### No root progress.json found"
    echo "Run \`/start-run\` or seed progress with the package seed_progress.py helper."
    echo ""
fi

MEM_COUNT=0
for memory_dir in "$PROJECT_ROOT/memory"; do
    if [ -d "$memory_dir" ]; then
        for memfile in MEMORY.md CONVENTIONS.md DECISIONS.md PATTERN_LIBRARY.md; do
            if [ -f "$memory_dir/$memfile" ]; then
                LINES=$(grep -cv '^[[:space:]]*$\|^[[:space:]]*#\|^<!--' "$memory_dir/$memfile" 2>/dev/null) || LINES=0
                if [ "${LINES:-0}" -gt "0" ]; then
                    MEM_COUNT=$((MEM_COUNT + LINES))
                fi
            fi
        done
    fi
done

if [ "$MEM_COUNT" -gt "0" ]; then
    echo "### Package memory: $MEM_COUNT entries"
else
    echo "### Package memory: empty"
fi

echo ""
echo "---"
