# Foundation Mission 1 — Drop-in files for `subtract0/agencyos`

Below are the ready-to-drop files for Mission 1 (Foundation Hardening & M4 Baseline). Each file is a code block you can copy into the repository at the path indicated. I created small, pragmatic implementations and CI skeletons so you can run the state-aware command safely.

---

## `scripts/repo_probe.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
out=/tmp/repo_probe.json
commit_sha=$(git rev-parse HEAD)
python - <<'PY'
import json,subprocess,sys
commit='''${commit_sha}'''
res={'commit_sha': commit, 'found_learning': False, 'found_agentcontext': False, 'found_store_memory': False}
# search
import subprocess
try:
    out = subprocess.check_output(['git','grep','-n','"def store_memory"'], universal_newlines=True)
    res['found_store_memory']=True
    res['store_memory_locs']=out.strip().splitlines()
except subprocess.CalledProcessError:
    pass
try:
    out = subprocess.check_output(['git','grep','-n','"learning.py"'], universal_newlines=True)
    res['found_learning']=True
    res['learning_locs']=out.strip().splitlines()
except subprocess.CalledProcessError:
    pass
try:
    out = subprocess.check_output(['git','grep','-n','"class AgentContext"'], universal_newlines=True)
    res['found_agentcontext']=True
    res['agentcontext_locs']=out.strip().splitlines()
except subprocess.CalledProcessError:
    pass
print(json.dumps(res, indent=2))
PY
```

---

## `models/verify_models.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
out=/tmp/model_choice.json
# Try Ollama first
models_json="[]"
if command -v ollama >/dev/null 2>&1; then
  models=$(ollama list --json 2>/dev/null || true)
  if [ -n "$models" ]; then
    # crude selection: largest by name heuristic; user will inspect
    echo "$models" > /tmp/ollama_list.json
  fi
fi
# Check HF cache (transformers cache path)
hf_cache_dir="$HOME/.cache/huggingface/hub"
# Emit a simple default file so pipeline continues
cat > "$out" <<JSON
{
  "model_id": "LOCAL_FALLBACK_30B",
  "model_hash": "unknown",
  "estimated_memory_bytes": 3200000000,
  "note": "Run this script on M4 to detect Ollama models. See /tmp/ollama_list.json if present."
}
JSON
echo "Wrote $out"
```

---

## `tools/model_smoke_test.py`
```python
#!/usr/bin/env python3
import json,sys,subprocess,time
out='/tmp/model_metrics.json'
# This is a smoke test that attempts to call a local model server or ollama
prompt='"def add(a,b):\\n    return a + b\\n"'
res={}
start=time.time()
try:
    # If ollama is present try a quick call
    if subprocess.run(['which','ollama'], stdout=subprocess.DEVNULL).returncode==0:
        # replace with actual model name if needed
        p = subprocess.run(['ollama','eval','--model','local','--prompt', 'print(1+1)'], capture_output=True, text=True, timeout=30)
        res['output']=p.stdout[:400]
        res['exit']=p.returncode
    else:
        res['note']='ollama not found'
except Exception as e:
    res['error']=str(e)
res['elapsed']=time.time()-start
with open(out,'w') as f:
    json.dump(res,f,indent=2)
print('wrote', out)
```

---

## `tools/adaptive_worker.py`
```python
#!/usr/bin/env python3
import argparse,psutil,subprocess,json,math

def probe_worker(cmd):
    # spawn a short-lived worker and measure peak RSS
    p = subprocess.Popen(cmd, shell=True)
    try:
        proc = psutil.Process(p.pid)
        ps=[]
        for _ in range(5):
            ps.append(proc.memory_info().rss)
        p.terminate()
    except Exception:
        p.terminate()
        return None
    return max(ps)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--job-cmd', default='pytest -q -k "not integration" --maxfail=1')
    args=parser.parse_args()
    if args.probe:
        rss = probe_worker(args.job_cmd)
        if rss is None:
            print('probe failed')
            raise SystemExit(1)
        total_ram = psutil.virtual_memory().total
        # default headroom 30GB
        headroom = 30 * 1024**3
        # default model reserved guess; will be overwritten after model probe
        model_reserved = 75 * 1024**3
        max_workers = math.floor((total_ram - model_reserved - headroom) / rss)
        max_workers = max(1, min(20, max_workers))
        cfg={'per_worker_rss': rss, 'total_ram': total_ram, 'max_workers': max_workers}
        with open('config/worker_limits.json','w') as f:
            json.dump(cfg,f,indent=2)
        print('wrote config/worker_limits.json', cfg)
```

---

## `shared/memory_api.py`
```python
from typing import Protocol, List, Optional, Dict

class MemoryAPI(Protocol):
    def store(self, memory: Dict) -> str: ...
    def retrieve(self, query: str, k: int = 10) -> List[Dict]: ...
    def supervise(self, memory_id: str, signal: str, actor: str, reason: Optional[str] = None) -> None: ...
```

---

## `shared/memory_adapter.py` (adapter wrapper - non-destructive)
```python
import uuid
from typing import Dict, Optional
from .memory_api import MemoryAPI

# This adapter assumes the repo has a store_memory(api) function somewhere.
# It will try to import common locations; if none found it raises informative error.

POSSIBLE_STORE="""
from shared import agent_context
agent_context.store_memory(...)
"""

class MemoryAdapter(MemoryAPI):
    def __init__(self, vectorstore=None):
        self.vectorstore = vectorstore
        # try to locate existing store function
        try:
            from shared.agent_context import store_memory as _store
            self._store = _store
            self._mode='wrap'
        except Exception:
            self._store = None
            self._mode='none'

    def store(self, memory: Dict) -> str:
        memory = dict(memory)
        memory.setdefault('memory_id', str(uuid.uuid4()))
        # ensure provenance and reinforcement keys exist
        memory.setdefault('provenance', {})
        memory.setdefault('reinforcement_signal', None)
        if self._store:
            # call existing store, passing through fields (best-effort)
            try:
                self._store(memory)
            except Exception as e:
                raise
        else:
            # fallback: append to local file (best-effort)
            with open('data/local_memory_store.jsonl','a') as f:
                f.write(json.dumps(memory)+'\n')
        return memory['memory_id']

    def retrieve(self, query: str, k: int = 10):
        # fallback simple search: scan local file
        results=[]
        try:
            with open('data/local_memory_store.jsonl') as f:
                for line in f:
                    obj=json.loads(line)
                    if query in str(obj.get('content','')):
                        results.append(obj)
                        if len(results)>=k: break
        except FileNotFoundError:
            pass
        return results

    def supervise(self, memory_id: str, signal: str, actor: str, reason: Optional[str]=None):
        # Append supervision event to an append-only file
        import time, json
        ev={'memory_id':memory_id,'signal':signal,'actor':actor,'reason':reason,'ts':time.time()}
        with open('data/supervision_events.log','a') as f:
            f.write(json.dumps(ev)+'\n')
```

---

## `shared/memory_filter.py`
```python
import re
SENSITIVE_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"), # AWS Access Key
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"), # Emails (optional)
    re.compile(r"(?:sk_live|sk_test)_[A-Za-z0-9]{24,}"),
]

def redact(text: str) -> str:
    out = text
    for pat in SENSITIVE_PATTERNS:
        out = pat.sub('[REDACTED]', out)
    return out

def filter_memory(mem: dict) -> dict:
    m=mem.copy()
    if 'content' in m and isinstance(m['content'], str):
        m['content']=redact(m['content'])
    return m
```

---

## `tools/metrics_exporter.py`
```python
#!/usr/bin/env python3
from prometheus_client import start_http_server, Gauge, Counter
import psutil, time, json

CPU = Gauge('system_cpu_percent','System CPU %')
RAM = Gauge('system_ram_available_bytes','System RAM available bytes')
MODEL_MEM = Gauge('model_mem_reserved_bytes','Model reserved bytes')
P50 = Gauge('model_p50_latency_ms','Model p50 latency ms')
P95 = Gauge('model_p95_latency_ms','Model p95 latency ms')
AGENT_ACTIVE = Gauge('agent_active_count','Number of running agents')
PR_CREATED = Counter('autogen_pr_created_total','Agent-created PRs')
SUPERVISION = Counter('supervision_events_total','Supervision events')
OOM = Counter('oom_events_total','OOM events')

if __name__=='__main__':
    start_http_server(9100)
    while True:
        CPU.set(psutil.cpu_percent())
        RAM.set(psutil.virtual_memory().available)
        # model metrics should be updated by model probe integration; here use placeholders
        MODEL_MEM.set(0)
        P50.set(0)
        P95.set(0)
        AGENT_ACTIVE.set(len([p for p in psutil.process_iter(['name']) if 'agent' in (p.info['name'] or '')]))
        time.sleep(5)
```

---

## `benchmarks/golden_dataset.json` (template)
```json
[
  {"id": "q1", "q": "What does function foo() do?", "a": "It returns the sum of x and y.", "memory_id": null},
  {"id": "q2", "q": "How should we handle error X?", "a": "Add a specific exception handler and log."}
]
```

---

## `benchmarks/benchmark_retrieval.py`
```python
#!/usr/bin/env python3
import json,sys
# minimal retrieval benchmark: placeholder
with open('benchmarks/golden_dataset.json') as f:
    gold=json.load(f)
print('Loaded', len(gold), 'queries')
# TODO: implement real P@K using MemoryAPI
print('P@K: placeholder')
```

---

## `.github/workflows/nightly-benchmarks.yml`
```yaml
name: Nightly Benchmarks
on:
  schedule:
    - cron: '0 3 * * *' # 03:00 UTC
  workflow_dispatch: {}
jobs:
  benchmarks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install deps
        run: python -m pip install -r requirements.txt || true
      - name: Run benchmarks
        run: |
          python benchmarks/benchmark_retrieval.py > /tmp/benchmarks_out.txt || true
          tar czf benchmarks_artifacts.tgz benchmarks || true
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: nightly-benchmarks
          path: benchmarks_artifacts.tgz
```

---

## `tools/agi_readiness_score.py`
```python
#!/usr/bin/env python3
import json,os
out='/tmp/agi_score.json'
score = {'tests':0,'memory':0,'model':0,'safety':0,'productivity':0}
# Tests: check /tmp/ci_status.txt
try:
    with open('/tmp/ci_status.txt') as f:
        txt=f.read()
    if 'PASS' in txt:
        score['tests']=30
except Exception:
    pass
# Memory: check supervision log exists
if os.path.exists('data/supervision_events.log'):
    score['memory']=15
# Model: if docs/model_choice.json exists
try:
    with open('docs/model_choice.json') as f:
        _=json.load(f)
    score['model']=15
except Exception:
    pass
# Safety: presence of PULL_REQUEST_TEMPLATE_AUTOGEN.md
if os.path.exists('.github/PULL_REQUEST_TEMPLATE_AUTOGEN.md'):
    score['safety']=15
# Productivity: placeholder until we have metrics
score['productivity']=0
score['total']=sum(score.values())
with open(out,'w') as f:
    json.dump({'score':score['total'],'breakdown':score}, f, indent=2)
print('wrote', out)
```

---

## `.github/PULL_REQUEST_TEMPLATE_AUTOGEN.md`
```markdown
<!-- AUTOGEN PR TEMPLATE -->
AGENT-META:
- memory_id: <UUID>
- agent_id: <agent-name>
- model_hash: <model-hash>
- workspace_sha: <workspace-sha>

## Summary

Describe the automated change.

## Checklist
- [ ] Tests pass
- [ ] Metadata included
- [ ] No secrets committed
```

---

## `scripts/revert_on_smoke_failure.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
# This script assumes GH CLI is configured
merged_pr=$1
if [ -z "$merged_pr" ]; then
  echo "Usage: $0 <merged-pr-number>"
  exit 1
fi
title="Revert PR #${merged_pr} - automated revert due to smoke failure"
body="Automated revert created because post-merge smoke tests failed."
# Create a revert branch (very simple approach)
branch="revert-pr-${merged_pr}"
git checkout -b "$branch"
# create a trivial commit (in practice use gh revert)
git commit --allow-empty -m "$title"
git push -u origin "$branch"
gh pr create --title "$title" --body "$body" --base main --head "$branch"
```

---

## `tests/test_memory_api.py` (basic smoke test)
```python
from shared.memory_api import MemoryAPI
from shared.memory_adapter import MemoryAdapter

def test_memory_store_and_supervise(tmp_path):
    adapter = MemoryAdapter()
    mem={'content':'hello','provenance':{'origin':'test'}}
    mid = adapter.store(mem)
    assert mid is not None
    adapter.supervise(mid,'approved','test')
    # assert supervision file contains the id
    with open('data/supervision_events.log') as f:
        s=f.read()
    assert str(mid) in s
```

---

## `pytest.ini`
```ini
[pytest]
addopts = -q
```

---

## `tests/conftest.py` (deterministic seed helper)
```python
import pytest
import random
import os

@pytest.fixture(autouse=True)
def set_seed():
    s=int(os.environ.get('PYTEST_SEED','42'))
    random.seed(s)
```

---

## `scripts/smoke_test.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
# Basic smoke test: run critical tests and quick lint
pytest -q tests/test_memory_api.py || exit 1
```

---

## `docs/model_choice.json` (template)
```json
{
  "model_id": "",
  "model_hash": "",
  "estimated_memory_bytes": 0,
  "note": "Populate after running models/verify_models.sh"
}
```

---

## `config/worker_limits.json` (template if not generated)
```json
{
  "per_worker_rss": 0,
  "total_ram": 137438953472,
  "max_workers": 1
}
```

---

# How to use these files (next steps)
1. Create a branch `foundation/<you>`.
2. Copy files into their paths in the repo (create directories: `tools`, `shared`, `scripts`, `benchmarks`, `docs`, `config`, `.github/workflows`, `tests`).
3. Run `bash scripts/repo_probe.sh` and commit `/tmp/repo_probe.json` into the draft branch if desired (for visibility).
4. Run `pytest -q` and iterate on the 3 failing tests; use the test harness helpers to seed determinism.
5. Run `python tools/model_smoke_test.py` on the M4 to produce `/tmp/model_metrics.json`.
6. Run `python tools/adaptive_worker.py --probe` to generate `config/worker_limits.json`.
7. Push the draft branch and open a Draft PR (manual review required).

---

If you want, I will now:
- produce a Git patch/PR diff ready to apply to `subtract0/agencyos` (you'll need to give me repo access or paste the repo structure), or
- walk you through applying these files step-by-step.

Which do you want next? (A) "Create PR patch" or (B) "Walk me through applying files"?

