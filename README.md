# NightShift Project

## Local Secrets Location

Sensitive files are stored outside the repo by default:

- `~/.config/agencyos/agency.env` (environment variables)
- `~/.config/agencyos/google/credentials.json` (Google OAuth client)
- `~/.config/agencyos/google/token.json` (Google OAuth tokens)

Set `AGENCY_ENV_FILE` or `AGENCY_CONFIG_DIR` to override these defaults.

## Timeout Protection

Long‑running tasks are now guarded by a **NightShiftWatchdog**.  
By default, `run_task` will abort any task that runs longer than **15 minutes**.  
You can override the timeout per call:
