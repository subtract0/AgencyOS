---
description: Aggressively prune codebase to achieve SpaceX-level efficiency
parameters:
  level: "aggressive" # Options: light, moderate, aggressive, nuclear
  target_branch: "feature/lean-codebase"
  preserve_tests: true
---

# Prune - Aggressive Codebase Cleanup

## Mission: Remove ALL Redundancy and Legacy Code

This command performs aggressive pruning of the codebase to achieve maximum efficiency. Only run this on a feature branch after establishing a stable baseline.

## Pre-Flight Checks

1. **Ensure on feature branch**: `git branch --show-current` must NOT be main/master
2. **All tests passing**: Run `python run_tests.py` - must be 100%
3. **Clean working directory**: No uncommitted changes
4. **Recent backup**: Tag current state before pruning

## Pruning Levels

### Level 1: Light (--level=light)
- Remove `.pyc` files and `__pycache__` directories
- Clear logs older than 7 days
- Remove empty directories
- Clean up whitespace and trailing newlines

### Level 2: Moderate (--level=moderate)
- Everything from Light, plus:
- Remove deprecated functions/classes marked with warnings
- Delete unused imports
- Remove commented-out code blocks
- Consolidate duplicate test files

### Level 3: Aggressive (--level=aggressive) [DEFAULT]
- Everything from Moderate, plus:
- Remove ALL backwards compatibility code
- Delete legacy pattern systems (core.patterns)
- Remove archived demos and examples
- Eliminate duplicate memory implementations
- Remove unused agents and tools
- Consolidate overlapping functionality

### Level 4: Nuclear (--level=nuclear)
- Everything from Aggressive, plus:
- Remove ALL tests except MasterTest
- Delete all documentation except README
- Remove all logging and telemetry
- Strip all comments from code
- Single implementation for everything

## Execution Workflow

### Phase 1: Analysis
```bash
# Count current files and lines
find . -name "*.py" | wc -l
find . -name "*.py" -exec wc -l {} + | tail -1

# Identify redundancy
grep -r "deprecated\|legacy\|backward.?compat\|TODO.*remove\|FIXME.*remove" --include="*.py"

# Find duplicate functionality
python -c "from tools.analyze_type_patterns import find_duplicates; find_duplicates()"
```

### Phase 2: Create Safety Branch
```bash
git checkout -b feature/lean-codebase
git tag pre-prune-backup
```

### Phase 3: Execute Pruning

#### Remove Deprecated Pattern Systems
- DELETE: `core/patterns.py` (UnifiedPatternStore)
- DELETE: `pattern_intelligence/migration.py`
- DELETE: All pattern conversion code
- KEEP: Only `pattern_intelligence/` module

#### Remove Duplicate Memory Systems
- DELETE: `agency_memory/memory_v2.py`
- DELETE: `agency_memory/swarm_memory.py`
- DELETE: `agency_memory/learning.py` (if redundant)
- KEEP: One clean implementation

#### Remove Backwards Compatibility
- DELETE: All backward compatibility fields
- DELETE: Legacy support code
- DELETE: Migration utilities
- DELETE: Deprecated API endpoints

#### Consolidate Agents
- DELETE: `subagent_example/` (just an example)
- MERGE: Overlapping agent functionality
- ENSURE: Single purpose per agent

#### Clean Tools
- DELETE: `agency_cli` legacy script
- DELETE: Duplicate edit tools
- DELETE: Unused telemetry aggregators
- ENSURE: One tool per function

#### Archive Cleanup
- DELETE: `demos/archive/` directory
- DELETE: `logs/archive/` older than 30 days
- DELETE: `.guardian/history/` (old analysis)
- DELETE: All `.bak` and `.old` files

#### Test Consolidation
- DELETE: `test_*_fixed.py` duplicate files
- DELETE: `test_*_legacy.py` files
- MERGE: Overlapping test coverage
- ENSURE: MasterTest covers all functionality

### Phase 4: Validation

```bash
# Run MasterTest to ensure nothing broke
python -m pytest tests/test_master_e2e.py -v

# Run full test suite (if preserved)
python run_tests.py

# Check that core demo still works
python demo_agency.py
```

### Phase 5: Measure Success

```bash
# Count files and lines after pruning
find . -name "*.py" | wc -l
find . -name "*.py" -exec wc -l {} + | tail -1

# Calculate reduction percentage
# Target: 50% reduction in files and lines
```

## Safety Mechanisms

1. **Automatic Backup**: Creates git tag before pruning
2. **Branch Protection**: Only runs on feature branches
3. **Test Validation**: Requires passing tests before and after
4. **Incremental Approach**: Can be run at different levels
5. **Revert Capability**: Easy rollback via git

## Expected Outcomes

- **50% fewer files** (Target: ~300 files from ~600)
- **60% less code** (Target: ~15K LOC from ~40K)
- **Zero backwards compatibility**
- **Single implementation patterns**
- **Faster test execution**
- **Clearer architecture**
- **Easier maintenance**

## Rollback Procedure

If pruning causes issues:

```bash
git checkout main
git branch -D feature/lean-codebase
git checkout pre-prune-backup -b feature/lean-codebase-v2
```

## Usage

```bash
# Default aggressive pruning
/prime prune

# Specific level
/prime prune --level=moderate

# Dry run (analysis only)
/prime prune --dry-run

# Preserve specific directories
/prime prune --preserve="demos,tools/legacy"
```

## Post-Prune Tasks

1. Update documentation to reflect removed features
2. Update CI/CD configs if paths changed
3. Create PR showing before/after metrics
4. Run performance benchmarks
5. Update README with new architecture

## Warning

This command makes DESTRUCTIVE changes. Always:
- Run on a feature branch
- Have a recent backup
- Validate with comprehensive tests
- Review changes before committing

---

*"Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away." - Antoine de Saint-Exupéry*