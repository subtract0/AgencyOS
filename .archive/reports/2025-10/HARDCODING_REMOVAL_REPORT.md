# Hardcoding Removal Report: Preference Learning Genericization

## Executive Summary

Identified and documented all user-specific "Alex" hardcoding in trinity_protocol preference learning files. This report details what must be genericized to create a reusable preference learning system in `shared/`.

## Files Analyzed

1. **trinity_protocol/preference_learning.py** (253 lines)
2. **trinity_protocol/preference_store.py** (397 lines)
3. **trinity_protocol/alex_preference_learner.py** (609 lines)

**Total**: 1,259 lines → Target: ~600 lines in shared/ (52% reduction)

---

## Hardcoding Issues Identified

### 1. File Names and Class Names (High Priority)

**Location**: `trinity_protocol/alex_preference_learner.py`
- **Line 39**: `class AlexPreferenceLearner` → Should be `PreferenceLearner`
- **Impact**: Class name is user-specific, preventing reuse

**Location**: `trinity_protocol/preference_store.py`
- **Lines 28-30**: Collection names hardcoded as `alex_responses`, `alex_preferences`, `alex_preference_history`
- **Impact**: Firestore collections are user-specific, not multi-user

### 2. Model Names (Medium Priority)

**Location**: `trinity_protocol/models/preferences.py`
- **Line 340**: `class AlexPreferences` → Should be `UserPreferences`
- **Impact**: Model name is user-specific

### 3. Docstring References (Low Priority but Pervasive)

**Location**: Multiple files throughout
- `preference_learning.py` Line 4: "Analyzes response patterns to learn when Alex says YES"
- `preference_learning.py` Line 35: "Learns Alex's preferences from HITL responses"
- `preference_store.py` Line 4: "Manages persistent storage of Alex's preferences"
- `alex_preference_learner.py` Line 4: "Analyzes response history to learn Alex's preferences"
- `alex_preference_learner.py` Line 41: "Learns Alex's preferences from response history"
- `alex_preference_learner.py` Line 74: "Article I: Complete context - analyzes ALL provided responses."
- `alex_preference_learner.py` Line 169: "Alex's response types"
- `alex_preference_learner.py` Line 451: "Generate actionable recommendations for ARCHITECT"

**Impact**: Documentation refers to specific user, should be generic

### 4. Hardcoded Context Keywords (Medium Priority)

**Location**: `trinity_protocol/alex_preference_learner.py`, Lines 418-422
```python
common_keywords = [
    "book", "coaching", "client", "project", "sushi",
    "meeting", "call", "email", "code", "system"
]
```

**Impact**: Keywords are Alex-specific personal preferences
**Solution**: Make keywords configurable via constructor parameter or config file

### 5. Firestore Collection Naming (High Priority)

**Location**: `trinity_protocol/preference_store.py`
- **Line 101**: `self.db.collection("alex_responses")`
- **Line 185**: `self.db.collection("alex_preferences")`
- **Line 191**: `self.db.collection("alex_preference_history")`
- **Line 205**: `self.db.collection("alex_preferences")`
- **Line 239**: `self.db.collection("alex_preference_history")`
- **Line 286**: `self.db.collection("alex_responses")`
- **Line 344**: `self.db.collection("alex_responses")`
- **Line 381**: `self.db.collection("alex_responses")`

**Impact**: All Firestore queries are hardcoded to "alex_*" collections
**Solution**: Use parameterized collection names: `{user_id}_responses`, `{user_id}_preferences`, `{user_id}_preference_history`

### 6. Comment References (Low Priority)

**Location**: `trinity_protocol/preference_store.py`
- Line 161: "# Update current preferences" (context: Alex-specific)
- Line 222: "# Extract preferences from snapshot" (context: Alex-specific)

---

## Genericization Strategy

### Phase 1: Core API Design
Create generic `PreferenceLearner` class with:
- **Constructor parameter**: `user_id: str` (replaces hardcoded "Alex")
- **Constructor parameter**: `context_keywords: Optional[List[str]] = None` (replaces hardcoded keywords)
- **Collection naming**: Dynamic based on `user_id`

### Phase 2: Model Renaming
- `AlexPreferences` → `UserPreferences` (with `user_id` field)
- `AlexPreferenceLearner` → `PreferenceLearner`
- Update all imports and references

### Phase 3: Storage Layer Genericization
- PreferenceStore: Accept `user_id` in constructor
- Collection names: `f"{user_id}_responses"`, `f"{user_id}_preferences"`, `f"{user_id}_preference_history"`
- Add `user_id` field to all stored records

### Phase 4: Documentation Updates
- Replace "Alex" with "user" in all docstrings
- Update examples to use generic terminology
- Add multi-user usage examples

---

## Consolidation Plan

### Files to Create
1. **`shared/preference_learning.py`** (~600 lines)
   - Consolidates all 3 files
   - Generic `PreferenceLearner` class
   - Generic `PreferenceStore` class
   - All utility functions

2. **`tests/unit/shared/test_preference_learning.py`** (~800 lines)
   - 30+ tests covering all functionality
   - Multi-user validation (Alice, Bob test cases)
   - NO hardcoding verification

### Files to Deprecate (Future)
- `trinity_protocol/preference_learning.py`
- `trinity_protocol/preference_store.py`
- `trinity_protocol/alex_preference_learner.py`

---

## Test-Driven Development Plan

### Test Categories (30+ tests)

#### 1. Initialization Tests (3 tests)
- Test initialization with different user IDs
- Test initialization with custom context keywords
- Test initialization with default parameters

#### 2. Response Recording Tests (4 tests)
- Test recording YES response
- Test recording NO response
- Test recording LATER response
- Test recording IGNORED response

#### 3. Preference Analysis Tests (8 tests)
- Test question type preference calculation
- Test timing preference calculation
- Test day of week preference calculation
- Test topic preference calculation
- Test contextual pattern detection
- Test confidence scoring
- Test trend detection (increasing/stable/decreasing)
- Test empty response handling

#### 4. Multi-User Isolation Tests (6 tests)
- Test Alice and Bob have separate preferences
- Test Alice's responses don't affect Bob's stats
- Test concurrent user preference storage
- Test user-specific Firestore collections
- Test user-specific recommendation generation
- Test cross-user data isolation

#### 5. Storage Tests (4 tests)
- Test in-memory storage
- Test SQLite persistence (if using SQLite backend)
- Test Firestore storage (mocked)
- Test preference snapshot versioning

#### 6. Recommendation Tests (3 tests)
- Test high-acceptance recommendations
- Test low-acceptance recommendations
- Test contextual pattern recommendations

#### 7. Integration Tests (2 tests)
- Test full observe → analyze → recommend flow
- Test message bus integration

---

## Success Criteria

✅ ZERO "Alex" references in code (only in historical context)
✅ All class/function names are generic
✅ Firestore collections parameterized by `user_id`
✅ Context keywords configurable (not hardcoded)
✅ 30+ tests, 100% passing
✅ Multi-user tests verify NO cross-user contamination
✅ 52% code reduction (1,259 → 600 lines)
✅ Result<T,E> pattern for error handling
✅ All functions <50 lines

---

## Implementation Order (TDD)

1. ✅ **This report**: Document hardcoding issues
2. ⏭️ **Write tests first**: 30+ tests in `tests/unit/shared/test_preference_learning.py`
3. ⏭️ **Implement**: Create `shared/preference_learning.py`
4. ⏭️ **Verify**: Run tests, ensure 100% pass rate
5. ⏭️ **Validate**: Multi-user validation (Alice, Bob scenarios)
6. ⏭️ **Commit**: With comprehensive commit message

---

**Next Action**: Write comprehensive test suite first (TDD mandate)
