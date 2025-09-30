# AUDITLEARN Prompt Versions

## Production Version (SpaceX Style)
**File**: `auditlearn_prompt.md`  
**Size**: 8.6KB (287 lines)  
**Style**: Token-efficient, Claude Opus style, zero fluff  
**Status**: ✅ Working copy for implementation

### What Was Removed
- Competition attribution and winner announcements
- Verbose explanations and philosophy sections
- Comparison tables and marketing copy
- Redundant headings and decorative elements
- Implementation checklists (moved to separate docs)

### What Was Kept (100% value retained)
✅ 8-step core loop (LISTEN → CLASSIFY → VALIDATE → ENRICH → SELF-VERIFY → PUBLISH → PERSIST → RESET)  
✅ Pattern heuristics with weights (failure, opportunity, user_intent)  
✅ Mathematical confidence formula: `base + Σ(keyword_matches × weight)`  
✅ JSON schema with validation requirements  
✅ Constitutional mandates (Articles I, II, IV)  
✅ Firestore persistence schema  
✅ Model configuration (Qwen 2.5-Coder 7B)  
✅ Complete implementation code examples  
✅ Adaptive threshold logic  
✅ MCP reference integration  
✅ Absolute rules

---

## Archive Version (Full Documentation)
**File**: `gemini_auditlearn_prompt.md`  
**Size**: 17KB (428 lines)  
**Style**: Complete with attribution, comparisons, checklists  
**Status**: 📦 Archived for reference

### Use Cases
- Understanding design rationale
- Training new team members
- Historical reference
- Competition documentation

---

## Efficiency Gain

```
Original: 428 lines (17KB)
SpaceX:   287 lines (8.6KB)
Reduction: 141 lines (33% smaller, 49% size reduction)
```

**Token savings**: ~2,000 tokens per context load

**Value lost**: 0% (all functional content preserved)

---

## Which Version to Use

| Task | Use Version |
|------|-------------|
| **Implementing the agent** | `auditlearn_prompt.md` ✅ |
| **Loading into LLM context** | `auditlearn_prompt.md` ✅ |
| **Quick reference** | `auditlearn_prompt.md` ✅ |
| **Understanding rationale** | `gemini_auditlearn_prompt.md` 📦 |
| **Training documentation** | `gemini_auditlearn_prompt.md` 📦 |

**Default**: Always use `auditlearn_prompt.md` unless you specifically need the historical context.

---

Last updated: 2025-09-30
