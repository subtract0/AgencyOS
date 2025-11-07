# DevContainer Validation Log

## Session: 2025-11-07
- Hardware: Mac Studio M4 Max (128 GB RAM)
- Docker Desktop 4.35 (Apple Silicon)
- Steps:
  1. Launch VS Code → "Reopen in Container"
  2. Devcontainer build time: 6m 45s (cached layers after initial run)
  3. Post-create hook `scripts/setup_dev_env.sh` completed in 2m 10s
  4. Verified services:
     - `vectorstore` (Postgres) responding on 5432
     - `vcoder` (Ollama) responding on 11434 (local model to be pulled manually)
  5. Ran smoke test inside container:
     ```bash
     pytest tests/test_memory_api.py::TestMemoryClass::test_memory_with_default_store -q
     ```
     Result: ✅ Pass
  6. Notes: Provide instructions for configuring Ollama model (vcoder-120b) via `ollama pull` once in container.

Next validation: capture provisioning time after pulling vcoder model to ensure <10 min cold start.
