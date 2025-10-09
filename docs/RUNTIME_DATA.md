# Runtime Data Management

## Overview

Agency OS follows a **stateless deployment model**: source code is in git, runtime data is created locally or in Docker volumes. This separation enables:

- **Clean git repository** (no runtime outputs tracked)
- **Docker/Kubernetes ready** (stateless containers)
- **Multi-environment deployment** (dev, staging, prod)
- **Easy scaling** (no local state dependencies)

## Runtime Data Types

### 1. SQLite Databases (*.db)

**Purpose**: Local data persistence for sessions, costs, patterns

**Location**: Project root directory

**Files**:
- `messages.db` - Chat/conversation history
- `trinity_costs.db` - API usage cost tracking
- `trinity_patterns.db` - Learned code patterns
- `hitl_protocol.db` - Human-in-the-loop interactions
- `demo_costs.db` - Demo session costs

**Docker Strategy**:
```yaml
# docker-compose.yml
services:
  agency:
    volumes:
      - agency_data:/app/data
volumes:
  agency_data:
```

**Runtime Creation**:
```python
# Databases are auto-created on first run
from core.telemetry import get_db_connection

conn = get_db_connection()  # Creates messages.db if not exists
```

### 2. JSONL Event Logs

**Purpose**: Telemetry, monitoring, audit trails

**Location**: `logs/` directory

**Files**:
- `logs/autonomous_healing/constitutional_violations.jsonl` - Quality violations
- `logs/constitutional_telemetry/events_YYYYMMDD.jsonl` - Daily telemetry
- `logs/telemetry/events-YYYYMMDD.jsonl` - System events

**Docker Strategy**:
```yaml
services:
  agency:
    volumes:
      - ./logs:/app/logs  # Mount logs directory
```

**Log Rotation**:
```bash
# Logs rotate daily (YYYYMMDD suffix)
# Clean up old logs:
find logs/ -name "*.jsonl" -mtime +30 -delete
```

### 3. Benchmark Results

**Purpose**: Performance testing output

**Location**: `benchmark_results/`

**Files**:
- `results_YYYYMMDD_HHMMSS.jsonl` - Timestamped benchmark runs

**Usage**:
```bash
# Run benchmarks
python scripts/benchmark.py

# Results saved to benchmark_results/ (gitignored)
```

### 4. Test Snapshots

**Purpose**: Mutation snapshot testing artifacts

**Location**: `logs/snapshots/`

**Files**:
- `logs/snapshots/YYYYMMDD_HHMMSS_*/manifest.json`
- `logs/snapshots/YYYYMMDD_HHMMSS_*/files/*`

**Cleanup**:
```bash
# Auto-cleaned by test framework
# Manual cleanup if needed:
rm -rf logs/snapshots/*
```

## Docker Deployment

### Dockerfile Example

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy source code only (no runtime data)
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create runtime data directories
RUN mkdir -p /app/data /app/logs /app/benchmark_results

# Run application
CMD ["python", "agency.py", "run"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  agency:
    build: .
    volumes:
      # Runtime data volumes (not in git)
      - agency_data:/app/data
      - agency_logs:/app/logs
      - agency_benchmarks:/app/benchmark_results
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - USE_LOCAL_MODEL=false
      - FRESH_USE_FIRESTORE=false

volumes:
  agency_data:
  agency_logs:
  agency_benchmarks:
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: agency-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agency
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: agency
        image: agency:latest
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: agency-data
      - name: logs
        emptyDir: {}  # Ephemeral logs (ship to logging service)
```

## Environment-Specific Configuration

### Local Development

```bash
# Runtime data created in project directory
ls -la *.db logs/
```

### CI/CD (GitHub Actions)

```yaml
# .github/workflows/test.yml
jobs:
  test:
    steps:
      - name: Run tests
        run: python run_tests.py --run-all
        env:
          SKIP_SPEC_TRACEABILITY: "true"
          USE_MOCK_LLM: "true"

      # Runtime data auto-cleaned after test run (ephemeral)
```

### Production

```bash
# Docker volumes for persistent data
docker volume ls
# DRIVER    VOLUME NAME
# local     agency_data
# local     agency_logs
```

## Data Migration

### Exporting Data

```bash
# Backup databases
tar -czf agency-data-$(date +%Y%m%d).tar.gz *.db logs/

# Copy to new environment
scp agency-data-20251009.tar.gz user@server:/backups/
```

### Importing Data

```bash
# Extract in new environment
tar -xzf agency-data-20251009.tar.gz

# Verify
ls -la *.db logs/
```

## Cleanup Commands

### Local Cleanup

```bash
# Remove all runtime data (start fresh)
rm -f *.db
rm -rf logs/*.jsonl logs/snapshots/
rm -rf benchmark_results/*.jsonl

# Re-run application (auto-creates fresh databases)
python agency.py run
```

### Docker Cleanup

```bash
# Remove volumes (destructive!)
docker-compose down -v

# Restart fresh
docker-compose up
```

## Monitoring & Observability

### Log Aggregation (Production)

```yaml
# Fluentd/Logstash pipeline
services:
  agency:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: "localhost:24224"
        tag: "agency.logs"
```

### Database Metrics

```python
# Monitor database size
import os

db_files = ["messages.db", "trinity_costs.db", "trinity_patterns.db"]
for db in db_files:
    if os.path.exists(db):
        size_mb = os.path.getsize(db) / (1024 * 1024)
        print(f"{db}: {size_mb:.2f} MB")
```

## Best Practices

### ✅ DO

- Mount runtime data as Docker volumes
- Use environment variables for configuration
- Implement log rotation (daily, size-based)
- Back up databases before major upgrades
- Monitor database growth (set alerts)

### ❌ DON'T

- Commit runtime data to git (security, bloat)
- Hardcode file paths (use relative paths)
- Store secrets in databases (use environment variables)
- Mix source code with runtime data in same directory
- Rely on local state in multi-instance deployments

## Troubleshooting

### Database Locked

```bash
# SQLite database locked error
# Solution: Close all connections
killall python
rm -f *.db-journal  # Remove journal files
```

### Missing Data After Deployment

```bash
# Check volume mounts
docker inspect agency | jq '.[0].Mounts'

# Verify data exists in volume
docker run --rm -v agency_data:/data busybox ls -la /data
```

### Log Files Growing Too Large

```bash
# Implement rotation in application
# Or use external log rotation:
# /etc/logrotate.d/agency
/app/logs/*.jsonl {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## Summary

**Git tracks**: Source code, configuration templates, documentation
**Runtime creates**: Databases, logs, benchmarks, snapshots
**Docker mounts**: Persistent volumes for data, ephemeral volumes for logs

This separation ensures clean deployments, easy scaling, and stateless architecture.

---

**See Also**:
- `.gitignore` - Runtime file exclusions
- `.dockerignore` - Docker build exclusions
- `docker-compose.yml` - Local Docker setup
- `docs/CI_CD_TIERED_ARCHITECTURE.md` - CI/CD strategy
