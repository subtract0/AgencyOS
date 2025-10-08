---
description: Gain a general understanding of the Agency codebase with a focus on improvements
settingSources: [project]
---

# Prime Claude Code

Execute the `Run`, `Read` and `Report` sections to understand the codebase then summarize your understanding.

## SDK Configuration

This command automatically loads:
- **Project settings** from `.claude/settings.json` (agents, tools, MCP servers)
- **Agent definitions** from `.claude/agents/`
- **Command definitions** from `.claude/commands/`

The `settingSources: [project]` frontmatter enables this automatic context loading.

## Run

Read and execute the .claude/commands/prime.md file top to bottom.

## Read

.claude/commands/**
.claude/agents/**
.claude/contexts/**
.claude/settings.json
CLAUDE.md
agency.py
docs/HARDWARE_OPTIMIZATION.md
specs/**
plans/**
tools/**
shared/**

## Report

Summarize your understanding of the codebase with focus on:
- **Hardware architecture**: M4 Pro 48GB constraints, memory budgets, Metal GPU optimization
- Overall Agency architecture and agent orchestration
- Available prime commands and their purposes
- Agent capabilities and specializations
- Tool infrastructure and shared utilities
- Quality enforcement and constitutional compliance
- Memory and context management systems
- **Local model optimization**: qwen3-coder:30b (Q4_K_M + Q8_0 KV cache), 37GB total
- Development workflow and best practices
- **Memory-aware execution**: 3 test workers max with local model, cloud fallback logic