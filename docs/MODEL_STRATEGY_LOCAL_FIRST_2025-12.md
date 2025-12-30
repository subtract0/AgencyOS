# AgencyOS Model Strategy (Local-First, M4 Max 128GB)

## Goals
- Snap‑fast voice + tool control with zero cloud cost.
- High‑IQ fallback for deep tasks without blocking the fast path.
- Safe, HITL-friendly life automation; offline path when required.

## Proposed Split-Brain Stack (per role)
- **Orchestrator (fast, tool-native)**: `nvidia/Nemotron-Orchestrator-8B` (GGUF/MLX). Purpose-built for function calling; 5‑10x faster than 70B.
- **General midbrain (balanced)**: `NousResearch/Hermes-4.3-36B` (GGUF/MLX). Creative/coverage without heavy latency.
- **Reasoner (deep)**: Keep `Llama 3.1 70B` (or upgrade to `INTELLECT-3 106B` only for queued “Deep Thought” tasks).
- **RAG reader (niche)**: `Apple CLaRa-7B-Instruct` for large-context doc QA if needed.
- **Offline tiny STS loop**: whisper.cpp (small/int8) + 1–3B Q4 LLM + piper/onnx TTS for no-network/privacy runs (<2GB RAM).

## Model Residency & Memory Policy (M4 Max 128GB)
- Limit resident models to ~100GB total weights; prefer shared mmap when running multiple of the same family.
- Recommended resident sets:
  - **Default**: Nemotron-8B + Hermes-36B (+ tiny STS) → leaves headroom.
  - **Deep**: Hermes-36B + Llama70B (or INTELLECT-3) but never >2 heavy models at once.
  - **Offline**: Tiny STS stack only; all network calls blocked.
- Expose a `MODEL_PROFILE` env: `fast`, `balanced`, `deep`, `offline` to switch sets cleanly.

## Routing Rules (deterministic, low-friction)
- Voice / tool calls / short-turn tasks → Nemotron-8B.
- Creative/general chat → Hermes-36B (fallback to Nemotron if absent).
- “Deep Thought” / research / heavy coding → queue to Llama70B or INTELLECT-3; run asynchronously to avoid blocking voice.
- Doc QA (big context) → CLaRa-7B (RAG pipeline) or Hermes with RAG if CLaRa unavailable.
- Offline flag (`OFFLINE_MODE=true`) → force tiny STS stack; forbid external HTTP; reject tool calls that require network.

## Integration Steps (developer checklist)
1) **Model plumbing**
   - Add `MODEL_PROFILE` and per-role model URIs in config.
   - Implement a lightweight router that selects orchestrator/general/reasoner based on intent tags (`tool_call`, `creative`, `deep`).
   - Add health checks + memory guard: refuse to load >100GB total; unload midbrain when starting deep mode if needed.
2) **Nemotron orchestration**
   - Convert Nemotron-8B to GGUF/MLX; add to model launcher scripts.
   - Update tool-calling prompts to native JSON/function-call format; add a small validation shim before execution.
   - Add 5–10 golden tool-call tests (delete email, move file, schedule event) to ensure parse/apply correctness.
3) **Offline STS path**
   - Wire whisper.cpp small/int8 + tiny 1–3B Q4 + piper/onnx; add `OFFLINE_MODE` guard that blocks network.
   - Add RAM-budget test (<2GB) and mocked audio round-trip test.
4) **Life-OS productionization**
   - CalendarTool → Google Calendar API; EmailTool → SMTP/Gmail with HITL confirmation; BrowserTool → Playwright (headless) with HITL prompts for risky ops.
   - Seed Night Shift tasks for real API wiring; add 2–3 E2E mocked tests for life flows.
5) **Agent Evolution loop**
   - Schedule weekly AgentEvolutionOrchestrator via Night Shift; auto-apply low-risk doc/test improvements; queue higher-risk for review.
   - Log evolution outcomes to CMP/VectorStore; track acceptance rate.
6) **Test posture**
   - Fast: sequential on macOS, `--max-duration` documented (e.g., 2400s). Legacy excluded by default.
   - Smoke bundle for Night Shift pre-flight.
   - Weekly legacy/slow sweep on Linux with xdist; prune/skip obsolete legacy tests.

## No-go / Safety
- Keep adaptive cloud routing disabled by default; enable only with per-agent caps.
- Explicitly exclude decensoring tools (e.g., heretic) from the toolchain.
- Enforce HITL for life actions; enforce no-network when `OFFLINE_MODE=true`.

## Immediate Low-Hanging Wins (do first)
- Stand up Nemotron-8B as default orchestrator and verify 5–10 tool-call golden tests.
- Add `MODEL_PROFILE` switch + memory guard; document default profiles.
- Ship the offline STS guardrails (even with mocked models) + RAM-budget test.
- Wire life tools to real APIs with HITL and add the first E2E mock test.
