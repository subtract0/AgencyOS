#!/bin/bash
# Memory monitoring script for training sessions

echo "=== Training Memory Monitor ==="
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    # Get memory stats
    vm_stat_output=$(vm_stat)

    # Parse vm_stat (page size is 16384 bytes on M-series Macs)
    PAGE_SIZE=16384

    free_pages=$(echo "$vm_stat_output" | grep "Pages free" | awk '{print $3}' | tr -d '.')
    active_pages=$(echo "$vm_stat_output" | grep "Pages active" | awk '{print $3}' | tr -d '.')
    inactive_pages=$(echo "$vm_stat_output" | grep "Pages inactive" | awk '{print $3}' | tr -d '.')
    wired_pages=$(echo "$vm_stat_output" | grep "Pages wired" | awk '{print $4}' | tr -d '.')

    # Calculate GB
    free_gb=$(echo "scale=2; $free_pages * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)
    active_gb=$(echo "scale=2; $active_pages * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)
    inactive_gb=$(echo "scale=2; $inactive_pages * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)
    wired_gb=$(echo "scale=2; $wired_pages * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)
    used_gb=$(echo "scale=2; $active_gb + $wired_gb" | bc)

    # Memory pressure (approximation)
    total_mem=48
    used_percent=$(echo "scale=1; ($used_gb / $total_mem) * 100" | bc)

    # Color coding based on usage
    if (( $(echo "$used_percent > 85" | bc -l) )); then
        status="🔴 HIGH"
    elif (( $(echo "$used_percent > 70" | bc -l) )); then
        status="🟠 MODERATE"
    else
        status="🟢 NORMAL"
    fi

    # Display
    clear
    echo "=== Training Memory Monitor ==="
    echo "$(date '+%H:%M:%S') - Status: $status"
    echo ""
    echo "Memory Usage (48GB total):"
    echo "  Active:   ${active_gb} GB"
    echo "  Wired:    ${wired_gb} GB"
    echo "  Inactive: ${inactive_gb} GB"
    echo "  Free:     ${free_gb} GB"
    echo ""
    echo "  Used:     ${used_gb} GB (${used_percent}%)"
    echo ""

    # Check for Python training process
    training_pid=$(pgrep -f "train_esper31_qlora_mac.py")
    if [ ! -z "$training_pid" ]; then
        echo "Training process PID: $training_pid"

        # Get process memory (if available)
        ps_mem=$(ps -o rss= -p $training_pid 2>/dev/null)
        if [ ! -z "$ps_mem" ]; then
            proc_gb=$(echo "scale=2; $ps_mem / 1024 / 1024" | bc)
            echo "Training process: ${proc_gb} GB"
        fi
    else
        echo "⚠️  Training process not found"
    fi

    echo ""
    echo "Press Ctrl+C to stop monitoring"

    sleep 10
done
