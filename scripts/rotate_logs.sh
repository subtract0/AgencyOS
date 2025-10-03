#!/bin/bash
# Log Rotation Script for Agency OS
# Compresses old session logs and removes outdated telemetry

set -e

echo "🔄 Starting log rotation..."

# Archive session logs older than 30 days
echo "📦 Archiving session logs (>30 days)..."
archived_count=$(find logs/sessions -name "*.md" -mtime +30 2>/dev/null | wc -l | tr -d ' ')
if [ "$archived_count" -gt 0 ]; then
    find logs/sessions -name "*.md" -mtime +30 -exec gzip {} \;
    echo "   ✅ Archived $archived_count session logs"
else
    echo "   ℹ️  No session logs older than 30 days"
fi

# Clean up old telemetry logs (>90 days)
echo "🗑️  Removing telemetry logs (>90 days)..."
deleted_count=$(find logs/telemetry -name "*.jsonl" -mtime +90 2>/dev/null | wc -l | tr -d ' ')
if [ "$deleted_count" -gt 0 ]; then
    find logs/telemetry -name "*.jsonl" -mtime +90 -delete
    echo "   ✅ Deleted $deleted_count telemetry logs"
else
    echo "   ℹ️  No telemetry logs older than 90 days"
fi

# Archive constitutional violations log if large
violations_log="logs/autonomous_healing/constitutional_violations.jsonl"
if [ -f "$violations_log" ]; then
    size=$(wc -c < "$violations_log" | tr -d ' ')
    if [ "$size" -gt 50000 ]; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        cp "$violations_log" "${violations_log}.${timestamp}"
        gzip "${violations_log}.${timestamp}"
        echo "" > "$violations_log"
        echo "   ✅ Archived constitutional violations log (${size} bytes)"
    fi
fi

echo ""
echo "✅ Log rotation complete!"
echo ""
echo "Current disk usage:"
du -sh logs/sessions logs/telemetry logs/autonomous_healing 2>/dev/null
