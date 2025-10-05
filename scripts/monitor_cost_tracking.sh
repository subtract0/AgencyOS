#!/bin/bash
# Cost Tracking Monitoring Script for Trinity Benchmark
# Monitors real-time cost accumulation during 10-task benchmark

DB_PATH="/Users/am/Code/Agency/trinity_costs.db"
WATCH_INTERVAL=10  # seconds

echo "=== Trinity Cost Tracking Monitor ==="
echo "Database: $DB_PATH"
echo "Refresh interval: ${WATCH_INTERVAL}s"
echo ""

# Check database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ ERROR: Database not found at $DB_PATH"
    echo "Expected location: $DB_PATH"
    echo "Alternative: ~/.trinity-local/trinity_costs.db"
    exit 1
fi

# Function to display real-time stats
monitor_costs() {
    clear
    echo "=== TRINITY COST TRACKING DASHBOARD ==="
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Overall statistics
    echo "--- OVERALL STATISTICS ---"
    sqlite3 "$DB_PATH" "SELECT
        COUNT(*) as total_calls,
        PRINTF('$%.4f', SUM(cost_usd)) as total_cost,
        SUM(input_tokens + output_tokens) as total_tokens,
        PRINTF('%.1f%%', AVG(success) * 100) as success_rate
    FROM llm_calls;"
    echo ""

    # Tier distribution
    echo "--- TIER DISTRIBUTION (ALL TIME) ---"
    sqlite3 "$DB_PATH" -column -header "SELECT
        COALESCE(model_tier, 'UNKNOWN') as tier,
        COUNT(*) as calls,
        PRINTF('%.2f%%', COUNT(*) * 100.0 / (SELECT COUNT(*) FROM llm_calls)) as pct_calls,
        PRINTF('$%.6f', SUM(cost_usd)) as cost,
        SUM(input_tokens) as tokens_in,
        SUM(output_tokens) as tokens_out
    FROM llm_calls
    GROUP BY model_tier
    ORDER BY calls DESC;"
    echo ""

    # Recent activity (last 5 minutes)
    echo "--- RECENT ACTIVITY (Last 5 Minutes) ---"
    sqlite3 "$DB_PATH" -column -header "SELECT
        COALESCE(model_tier, 'UNKNOWN') as tier,
        COUNT(*) as calls,
        PRINTF('$%.6f', SUM(cost_usd)) as cost,
        SUM(input_tokens + output_tokens) as tokens
    FROM llm_calls
    WHERE timestamp > datetime('now', '-5 minutes')
    GROUP BY model_tier
    ORDER BY tier;"
    echo ""

    # Agent breakdown
    echo "--- AGENT USAGE ---"
    sqlite3 "$DB_PATH" -column -header "SELECT
        agent,
        COUNT(*) as calls,
        PRINTF('$%.4f', SUM(cost_usd)) as cost
    FROM llm_calls
    GROUP BY agent
    ORDER BY calls DESC
    LIMIT 10;"
    echo ""

    # Cost savings calculation (local vs cloud)
    echo "--- COST SAVINGS ANALYSIS ---"
    sqlite3 "$DB_PATH" "SELECT
        PRINTF('Local calls: %d', COUNT(CASE WHEN model_tier LIKE '%local%' THEN 1 END)) as local,
        PRINTF('Cloud calls: %d', COUNT(CASE WHEN model_tier NOT LIKE '%local%' AND model_tier IS NOT NULL THEN 1 END)) as cloud,
        PRINTF('Actual cost: $%.4f', SUM(cost_usd)) as actual,
        PRINTF('If 100%% cloud: $%.4f', COUNT(*) * 0.05) as cloud_estimate,
        PRINTF('Savings: $%.4f', (COUNT(*) * 0.05) - SUM(cost_usd)) as savings
    FROM llm_calls;"
    echo ""

    # Check for anomalies
    echo "--- ANOMALIES DETECTED ---"

    # Check for local tier with non-zero cost
    LOCAL_COST=$(sqlite3 "$DB_PATH" "SELECT SUM(cost_usd) FROM llm_calls WHERE model_tier LIKE '%local%' AND cost_usd > 0;")
    if [ ! -z "$LOCAL_COST" ] && [ "$LOCAL_COST" != "0" ]; then
        echo "⚠️  WARNING: Local tier has non-zero cost ($LOCAL_COST) - should be $0.00"
    fi

    # Check for NULL tiers
    NULL_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM llm_calls WHERE model_tier IS NULL;")
    if [ "$NULL_COUNT" -gt 0 ]; then
        echo "⚠️  WARNING: $NULL_COUNT calls have NULL tier (integration issue)"
    fi

    # Check for stale data
    LAST_TIMESTAMP=$(sqlite3 "$DB_PATH" "SELECT MAX(timestamp) FROM llm_calls;")
    echo "Last activity: $LAST_TIMESTAMP"

    # Check if no local usage
    LOCAL_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM llm_calls WHERE model_tier LIKE '%local%';")
    if [ "$LOCAL_COUNT" -eq 0 ]; then
        echo "❌ CRITICAL: Zero local tier usage detected"
        echo "   Local-first escalation may not be working!"
    fi

    echo ""
    echo "Press Ctrl+C to stop monitoring"
}

# Main loop
if [ "$1" == "--watch" ]; then
    while true; do
        monitor_costs
        sleep $WATCH_INTERVAL
    done
else
    monitor_costs
fi
