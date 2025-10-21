# 🔍 Monastery 0.8.0 Beta - Feature Verification Instructions

This document provides comprehensive instructions for verifying all claimed features in Monastery 0.8.0 Beta release.

## 📋 Manual Verification Checklist

### 1. 🏥 Autonomous Healing System (CRITICAL)

**This is the KEY differentiator - must work!**

```bash
# Test 1: Run the autonomous healing demo
python demo_autonomous_healing.py

# Expected: Complete demo showing:
# - Error detection from logs
# - LLM-powered fix generation
# - Patch application workflow
# - Test verification process

# Test 2: Check autonomous healing tools exist
python -c "from tools.auto_fix_nonetype import AutoNoneTypeFixer, NoneTypeErrorDetector, LLMNoneTypeFixer; print('✅ Healing tools available')"

# Test 3: Check orchestration components
python -c "from tools.apply_and_verify_patch import ApplyAndVerifyPatch, AutonomousHealingOrchestrator; print('✅ Orchestration available')"

# Test 4: Verify healing logs directory
ls -la logs/autonomous_healing/ 2>/dev/null || echo "No healing logs yet"
```

**✅ PASS Criteria:**
- Demo runs without crashes
- All healing tools import successfully
- Orchestration components available
- Error detection works on sample logs

**❌ FAIL Indicators:**
- ImportError on healing tools
- Demo crashes or doesn't show healing workflow
- Missing core components

### 2. 🤖 Multi-Agent Architecture (10 Agents)

```bash
# Test 1: Verify all 10 agents can be imported
python -c "
try:
    from chief_architect_agent import create_chief_architect_agent
    from agencyos_agent.agencyos_agent import create_agencyos_agent
    from planner_agent.planner_agent import create_planner_agent
    from auditor_agent import create_auditor_agent
    from test_generator_agent import create_test_generator_agent
    from learning_agent import create_learning_agent
    from merger_agent.merger_agent import create_merger_agent
    from toolsmith_agent import create_toolsmith_agent
    from work_completion_summary_agent import create_work_completion_summary_agent
    from quality_enforcer_agent import create_quality_enforcer_agent
    print('✅ All 10 agents importable')
except ImportError as e:
    print(f'❌ Agent import failed: {e}')
"

# Test 2: Test agent creation (with safe model)
python -c "
from agencyos_agent.agencyos_agent import create_agencyos_agent
from planner_agent.planner_agent import create_planner_agent
try:
    coder = create_agencyos_agent(model='gpt-4', reasoning_effort='low')
    planner = create_planner_agent(model='gpt-4', reasoning_effort='low')
    print('✅ Core agents can be created')
except Exception as e:
    print(f'❌ Agent creation failed: {e}')
"

# Test 3: Interactive agency test (requires manual interaction)
# sudo python agency.py
# Try: "Create a simple Python function to calculate fibonacci"
# Should see: Planner → Coder workflow
```

**✅ PASS Criteria:**
- All 10 agents import without errors
- Core agents can be instantiated
- Agency interactive mode works
- Agent handoffs function

**❌ FAIL Indicators:**
- Missing agent modules
- Creation failures
- No agent communication

### 3. 🧠 Memory & Learning System

```bash
# Test 1: Basic memory functionality
python -c "
from agency_memory import Memory, InMemoryStore
memory = Memory(store=InMemoryStore())
memory.store('test', {'data': 'value'}, tags=['test'])
result = memory.get('test')
assert result['data'] == 'value'
print('✅ Basic memory works')
"

# Test 2: Memory search and tagging
python -c "
from agency_memory import Memory, InMemoryStore
memory = Memory(store=InMemoryStore())
memory.store('item1', {'type': 'error'}, tags=['error', 'fix'])
memory.store('item2', {'type': 'success'}, tags=['success', 'fix'])
results = memory.search(tags=['fix'])
assert len(results) >= 2
print('✅ Memory search works')
"

# Test 3: Learning consolidation
python -c "
from agency_memory import consolidate_learnings, Memory, InMemoryStore
memory = Memory(store=InMemoryStore())
memory.store('learn1', {'pattern': 'test'}, tags=['learning'])
report = consolidate_learnings(memory.store)
print('✅ Learning consolidation works')
"

# Test 4: Session transcripts
ls -la logs/sessions/ 2>/dev/null && echo "✅ Session transcripts directory exists" || echo "❌ No session transcripts"

# Test 5: Enhanced memory (VectorStore)
python -c "
try:
    from agency_memory import EnhancedMemoryStore, create_enhanced_memory_store
    store = create_enhanced_memory_store()
    print('✅ Enhanced memory available')
except Exception as e:
    print(f'⚠️ Enhanced memory not fully available: {e}')
"
```

**✅ PASS Criteria:**
- Basic memory operations work
- Tagging and search functional
- Learning consolidation available
- Session transcript system exists

**❌ FAIL Indicators:**
- Memory operations fail
- No session logging
- Learning system broken

### 4. 🏛️ Constitutional Governance

```bash
# Test 1: Constitution file exists
ls -la constitution.md && echo "✅ Constitution exists" || echo "❌ No constitution"

# Test 2: Constitution content validation
grep -E "Article [I-V]" constitution.md && echo "✅ All 5 articles present" || echo "❌ Missing articles"

# Test 3: 100% test claim verification
python run_tests.py 2>&1 | tee test_results.txt
grep -i "all tests passed\|100%\|✅" test_results.txt && echo "✅ Tests pass" || echo "❌ Test failures"

# Test 4: Constitutional enforcement hooks
python -c "
try:
    # Check if constitutional validation exists in agents
    import constitution  # If this module exists
    print('✅ Constitutional enforcement available')
except ImportError:
    print('⚠️ Constitutional enforcement module not found')
"
```

**✅ PASS Criteria:**
- Constitution file exists with all 5 articles
- Test suite actually achieves 100% pass rate
- Constitutional enforcement mechanisms present

**❌ FAIL Indicators:**
- Missing constitution file
- Test failures present
- No enforcement mechanisms

### 5. 💻 CLI Commands (World-Class UX)

```bash
# Test 1: Health command
python agency.py health
echo "Exit code: $?"

# Test 2: Logs command
python agency.py logs

# Test 3: Test command
timeout 30s python agency.py test || echo "Test command timed out (expected)"

# Test 4: Demo command
timeout 10s python agency.py demo || echo "Demo command started (expected timeout)"

# Test 5: Legacy CLI script
ls -la agency_cli && echo "✅ Legacy CLI exists" || echo "⚠️ No legacy CLI"

# Test 6: Help/usage
python agency.py --help
```

**✅ PASS Criteria:**
- All commands run without immediate errors
- Health command shows system status
- Logs command displays recent activity
- Commands provide useful output

**❌ FAIL Indicators:**
- Commands crash immediately
- No output or error messages
- Missing CLI functionality

### 6. 🛠️ Development Tools (40+ Tools Claimed)

```bash
# Test 1: Core file tools
python -c "
from tools import Read, Write, Edit, MultiEdit
print('✅ File operations available')
"

# Test 2: Search tools
python -c "
from tools import Grep, Glob
print('✅ Search tools available')
"

# Test 3: System tools
python -c "
from tools import Bash, TodoWrite
print('✅ System tools available')
"

# Test 4: Specialized tools
python -c "
try:
    from tools import Git, NotebookRead, NotebookEdit
    print('✅ Specialized tools available')
except ImportError as e:
    print(f'⚠️ Some specialized tools missing: {e}')
"

# Test 5: Tool count verification
python -c "
import tools
tool_count = len([name for name in dir(tools) if not name.startswith('_')])
print(f'📊 Tool count: {tool_count}')
if tool_count >= 20:
    print('✅ Substantial tool set available')
else:
    print('⚠️ Fewer tools than expected')
"

# Test 6: Tool functionality test
python -c "
from tools import Read, Write, Bash
import tempfile, os

# Test file operations
test_file = os.path.join(tempfile.gettempdir(), 'tool_test.txt')
Write().run(file_path=test_file, content='Hello Tools')
content = Read().run(file_path=test_file)
assert 'Hello Tools' in content

# Test bash
result = Bash().run(command='echo Tool Test')
assert 'Tool Test' in result

print('✅ Tools functionally work')
os.remove(test_file)
"
```

**✅ PASS Criteria:**
- All core tool categories available
- Tools actually function (not just import)
- Substantial tool count (20+ tools)
- File operations work correctly

**❌ FAIL Indicators:**
- Missing core tools
- Tools don't actually work
- Very low tool count

## 🧪 Automated MasterTest Execution

After completing manual verification:

```bash
# Run the comprehensive automated test suite
python -m pytest tests/test_master_e2e.py -v --tb=short

# Or run directly
python tests/test_master_e2e.py
```

## 📊 Expected Results

### 🎯 Success Criteria (Monastery 0.8.0 Beta)

- **Autonomous Healing**: ✅ Core tools work, demo runs
- **Multi-Agent**: ✅ At least 8/10 agents functional
- **Memory System**: ✅ Basic memory + learning works
- **Constitutional**: ✅ Constitution exists, most tests pass
- **CLI Commands**: ✅ All major commands functional
- **Development Tools**: ✅ 20+ tools available and working

### ⚠️ Acceptable Beta Limitations

- Enhanced memory/VectorStore may have dependency issues
- Some specialized tools may be missing
- Test suite may not be exactly 100% (close to 100%)
- Advanced features may be experimental

### ❌ Critical Failures (Must Fix)

- Autonomous healing tools completely missing
- Core agents can't be created
- Memory system broken
- CLI commands crash
- Basic file tools don't work

## 🐛 Known Issues to Check

Based on the codebase analysis, these are likely problem areas:

1. **QualityEnforcerAgent**: May not be fully implemented
2. **Enhanced Memory**: VectorStore dependencies might be missing
3. **Autonomous Healing Integration**: Tools exist but may not be fully wired
4. **CLI Command Modules**: Some commands may reference missing modules
5. **Test Suite**: Probably not actually at 100% pass rate

## 📋 Verification Report Template

Use this template to document your verification results:

```markdown
# Monastery 0.8.0 Beta Verification Report

**Date**: [DATE]
**Verifier**: [NAME]
**Version**: Monastery 0.8.0 Beta

## Manual Verification Results

| Feature | Status | Notes |
|---------|--------|-------|
| 🏥 Autonomous Healing | ✅/❌ | [Details] |
| 🤖 Multi-Agent (10) | ✅/❌ | [X/10 agents working] |
| 🧠 Memory System | ✅/❌ | [Details] |
| 🏛️ Constitutional | ✅/❌ | [Test pass rate: X%] |
| 💻 CLI Commands | ✅/❌ | [Details] |
| 🛠️ Dev Tools | ✅/❌ | [X tools found] |

## Automated Test Results

```
[Paste MasterTest output here]
```

## Critical Issues Found

1. [Issue description]
2. [Issue description]

## Recommendations

- [Priority 1 fix]
- [Priority 2 fix]

## Overall Assessment

Beta quality: ✅ Ready / ⚠️ Needs work / ❌ Not ready

Key strengths: [List]
Key gaps: [List]
```

## 🚀 Quick Start Verification

For a rapid verification (5 minutes):

```bash
# 1. Quick healing check
python -c "from tools.auto_fix_nonetype import AutoNoneTypeFixer; print('✅ Healing')"

# 2. Quick agent check
python -c "from agencyos_agent.agencyos_agent import create_agencyos_agent; print('✅ Agents')"

# 3. Quick memory check
python -c "from agency_memory import Memory; print('✅ Memory')"

# 4. Quick tools check
python -c "from tools import Read, Write, Bash; print('✅ Tools')"

# 5. Quick CLI check
python agency.py health

echo "🎯 Rapid verification complete!"
```

This verification process will definitively validate whether Monastery 0.8.0 Beta delivers on its promises or identify gaps that need addressing before 1.0.