#!/bin/bash
# Quick training monitor - run this in a separate terminal

echo "=== Esper3.1 Training Monitor ==="
echo "Watching: data/training_log_restart.txt"
echo "Press Ctrl+C to stop"
echo ""

# Show last 20 lines and follow
tail -f -n 20 data/training_log_restart.txt &
TAIL_PID=$!

# Monitor memory every 30 seconds
while true; do
    sleep 30
    clear
    echo "=== Training Monitor ($(date '+%H:%M:%S')) ==="
    echo ""

    # Last few lines of training
    echo "Last 5 lines:"
    tail -n 5 data/training_log_restart.txt 2>/dev/null || echo "Log not ready"
    echo ""

    # Memory status
    vm_stat_output=$(vm_stat)
    PAGE_SIZE=16384
    free_pages=$(echo "$vm_stat_output" | grep "Pages free" | awk '{print $3}' | tr -d '.')
    active_pages=$(echo "$vm_stat_output" | grep "Pages active" | awk '{print $3}' | tr -d '.')
    wired_pages=$(echo "$vm_stat_output" | grep "Pages wired" | awk '{print $4}' | tr -d '.')
    compressed=$(echo "$vm_stat_output" | grep "stored in compressor" | awk '{print $5}' | tr -d '.')

    free_gb=$(echo "scale=1; $free_pages * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)
    active_gb=$(echo "scale=1; $active_pages * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)
    wired_gb=$(echo "scale=1; $wired_pages * $PAGE_SIZE / 1024 / 1024 / 1024" | bc)

    echo "Memory: Free ${free_gb}GB | Active ${active_gb}GB | Wired ${wired_gb}GB"

    # Training process
    training_pid=$(pgrep -f "train_esper31_qlora_mac.py")
    if [ ! -z "$training_pid" ]; then
        ps_info=$(ps -o pcpu,pmem,etime -p $training_pid 2>/dev/null | tail -1)
        echo "Process: $ps_info"
    else
        echo "⚠️  Training process not found!"
    fi
    echo ""
done

# Cleanup
trap "kill $TAIL_PID 2>/dev/null" EXIT
