#!/usr/bin/env bash
# Hook: load-run-state (SessionStart)
# Reads the latest session.json and prints run context for immediate orientation.
set -euo pipefail

PROJECT_ROOT="$(pwd)"

echo "## Build Agent — Session Context"
echo ""

# Find the latest run
LATEST_RUN=$(ls -1d "$PROJECT_ROOT/state/run_id_"* 2>/dev/null | sort -r | head -1)

if [ -n "$LATEST_RUN" ] && [ -f "$LATEST_RUN/session.json" ]; then
    RUN_ID=$(basename "$LATEST_RUN")
    echo "### Active run: $RUN_ID"

    python3 -c "
import json, sys
try:
    with open('$LATEST_RUN/session.json') as f:
        s = json.load(f)
    print(f\"- Phase: {s.get('active_phase', 'unknown')}\")
    scope = s.get('scope_selection', {})
    selected = [k for k, v in scope.items() if v is True]
    if selected:
        print(f\"- Scope: {', '.join(selected)}\")
    platform = s.get('pipeline_platform', '')
    if platform:
        print(f\"- Pipeline platform: {platform}\")
    plan = s.get('planning_summary', {})
    if plan:
        lineage_gen = plan.get('lineage_generated', False)
        lineage_rec = plan.get('lineage_reconciled', False)
        if lineage_gen:
            status = 'reconciled' if lineage_rec else 'planned (not yet reconciled)'
            print(f\"- Lineage: {status}\")
    gen = s.get('generation_summary', {})
    if gen:
        completed = [k for k, v in gen.items() if v is True or (isinstance(v, dict) and v.get('status') == 'complete')]
        if completed:
            print(f\"- Generated: {', '.join(str(c) for c in completed)}\")
    verdict = s.get('input_quality_verdict', '')
    readiness = s.get('input_quality_readiness_percent', '')
    if verdict:
        print(f\"- Input verdict: {verdict} ({readiness}% readiness)\" if readiness else f\"- Input verdict: {verdict}\")
except Exception as e:
    print(f'- (Could not parse session.json: {e})')
" 2>/dev/null || echo "- (session.json parse failed)"
else
    echo "### No active run"
    echo "Run \`/start-build-run\` to begin."
fi

# Check memory
if [ -d "$PROJECT_ROOT/memory" ]; then
    MEM_COUNT=0
    for memfile in MEMORY.md CONVENTIONS.md DECISIONS.md PATTERN_LIBRARY.md; do
        if [ -f "$PROJECT_ROOT/memory/$memfile" ]; then
            LINES=$(grep -cv '^\s*$\|^\s*#\|^<!--' "$PROJECT_ROOT/memory/$memfile" 2>/dev/null || echo "0")
            if [ "$LINES" -gt "0" ]; then
                MEM_COUNT=$((MEM_COUNT + LINES))
            fi
        fi
    done
    if [ "$MEM_COUNT" -gt "0" ]; then
        echo ""
        echo "### Memory: $MEM_COUNT entries across memory/ files"
    fi
fi

echo ""
echo "---"
