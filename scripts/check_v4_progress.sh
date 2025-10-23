#!/bin/bash
# Quick V4 progress checker

echo "=== V4 Audit Progress ==="
echo ""

# Check if process is running
if ps -p 9921 > /dev/null 2>&1; then
    echo "✅ Status: RUNNING (PID 9921)"
    ps -p 9921 -o etime,rss | tail -1 | awk '{print "   Runtime: " $1 "   Memory: " int($2/1024) " MB"}'
else
    echo "❌ Status: STOPPED"
fi

echo ""

# Check state file
if [ -f .marathon_audit_v4_state.json ]; then
    TESTS=$(jq -r '.tests_analyzed // 0' .marathon_audit_v4_state.json 2>/dev/null)
    TOTAL=$(jq -r '.total_tests // 1200' .marathon_audit_v4_state.json 2>/dev/null)
    if [ "$TESTS" != "null" ] && [ "$TESTS" != "0" ]; then
        PCT=$((TESTS * 100 / TOTAL))
        echo "📊 Progress: $TESTS / $TOTAL tests ($PCT%)"

        # Estimate time remaining
        ELAPSED=$(ps -p 9921 -o etime= 2>/dev/null | awk -F: '{if (NF==3) print ($1*3600 + $2*60 + $3); else print ($1*60 + $2)}')
        if [ -n "$ELAPSED" ] && [ "$TESTS" -gt "0" ]; then
            RATE=$(echo "$TESTS / $ELAPSED" | bc -l)
            REMAINING=$(echo "($TOTAL - $TESTS) / $RATE / 60" | bc -l)
            printf "   ETA: %.0f minutes remaining\n" $REMAINING
        fi
    else
        echo "📊 Progress: Extracting test functions..."
    fi
else
    echo "📊 Progress: Starting up..."
fi

echo ""

# Check log file
LOG=$(ls -t v4_1200tests_*.log 2>/dev/null | head -1)
if [ -n "$LOG" ]; then
    SIZE=$(ls -lh "$LOG" | awk '{print $5}')
    echo "📝 Log: $LOG ($SIZE)"
    if [ -s "$LOG" ]; then
        echo ""
        echo "Last 10 lines:"
        tail -10 "$LOG"
    fi
else
    echo "📝 Log: Not created yet"
fi

echo ""
echo "=== Quick Commands ==="
echo "  Monitor live: tail -f $LOG"
echo "  Check again:  bash scripts/check_v4_progress.sh"
echo "  Kill if needed: kill 9921"
