# NightShift Project

## Timeout Protection

Long‑running tasks are now guarded by a **NightShiftWatchdog**.  
By default, `run_task` will abort any task that runs longer than **15 minutes**.  
You can override the timeout per call:
