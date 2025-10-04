# Specification: Style Distillery - Bottled Constitutional Consciousness

**Date**: 2025-10-04
**Status**: Draft
**Author**: Digital Muse Team
**Context**: Package Constitutional Consciousness as standalone tool for ANY codebase

---

## The Vision (From Gemini's Digital Muse)

**Everyone else**: Static linters that nag about syntax
**Style Distillery**: A mentor that learns your project's unique "flavor" and helps developers write code that feels like it belongs

**Not rules. Taste.**

---

## Goals

1. **One-Command Distillation**: Point at any repo, extract its coding DNA
2. **Git History as Training Data**: Learn patterns from actual decisions (commits/PRs)
3. **Precedent-Based Recommendations**: "Based on 47 similar decisions, YOU chose..."
4. **Self-Contained Package**: Works on any repo without modifying it
5. **Constitutional Evolution**: Generates living constitution from observed patterns

## Non-Goals

- Generic best practices (we learn YOUR practices)
- Real-time code generation (observation/learning only)
- Cloud dependency (100% local operation)
- Integration with existing linters (complementary, not replacement)

## Personas

### Primary: Tech Lead Managing Team Style
- **Need**: Onboard new devs to team's unwritten conventions
- **Pain**: "We don't use Redux here" said after 2 weeks of work
- **Workflow**: Run `muse distill`, new devs query before decisions

### Secondary: Solo Dev with Multiple Projects
- **Need**: Switch between projects without losing context
- **Pain**: "What pattern did I use for error handling in Project A?"
- **Workflow**: Distill each project, query for past decisions

### Tertiary: AI Researcher
- **Need**: Study how coding style evolves over project lifetime
- **Pain**: Manual git log analysis is tedious
- **Workflow**: Distill repo, export learning graphs

---

## Architecture

### The Distillation Pipeline

```
┌─────────────────────────────────────────────────────┐
│  INPUT: Git Repository                              │
│  - Commits (git log --all --stat)                  │
│  - PRs (gh api repos/owner/repo/pulls)             │
│  - Code Reviews (gh pr view --comments)            │
│  - File changes (git diff)                         │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  EXTRACTION: Pattern Mining                         │
│  1. Architectural Decisions                         │
│     - "Moved from Context → Redux in PR #47"       │
│     - "Refactored 12 functions to <50 lines"       │
│  2. Type Safety Evolution                           │
│     - "Eliminated Dict[Any] across 23 commits"     │
│     - "Added Pydantic models for all API inputs"   │
│  3. Testing Patterns                                │
│     - "100% coverage enforced since commit abc123"  │
│     - "AAA pattern in 94% of tests"                │
│  4. Error Handling Style                            │
│     - "Result<T,E> pattern adopted commit def456"   │
│     - "Replaced 47 try/catch with Result"          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  LEARNING: VectorStore Ingestion                    │
│  - Embed decisions as semantic vectors             │
│  - Tag by category (architecture, types, tests)    │
│  - Track confidence (frequency × recency)          │
│  - Store precedent citations (commit SHA, PR #)    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  OUTPUT: Living Constitution                        │
│  - Generated constitution.yaml                      │
│  - Precedent database (VectorStore)                │
│  - Decision recommendation API                      │
│  - Evolution timeline visualization                │
└─────────────────────────────────────────────────────┘
```

---

## User Experience

### Installation

```bash
# From PyPI (when released)
pip install style-distillery

# Or from GitHub
pip install git+https://github.com/subtract0/style-distillery.git
```

### Distillation (One Command)

```bash
# Point at any repo
muse distill /path/to/my-project

# With options
muse distill /path/to/my-project \
  --since "2024-01-01" \
  --min-confidence 0.7 \
  --output ./project-dna/
```

**Output**:
```
🔍 Analyzing git history...
   - 1,247 commits analyzed
   - 89 pull requests processed
   - 234 architectural decisions extracted

🧠 Learning patterns...
   - Architectural: 47 patterns (confidence: 0.85)
   - Type Safety: 23 patterns (confidence: 0.92)
   - Testing: 12 patterns (confidence: 0.88)
   - Error Handling: 8 patterns (confidence: 0.79)

📜 Generating constitution...
   ✓ constitution.yaml created
   ✓ Precedent database initialized (234 decisions)
   ✓ VectorStore ready for queries

✅ Style distilled to: ./project-dna/

Next steps:
  muse query "Should I use Redux or Context API?"
  muse precedent --similar "state management"
  muse evolution --topic "type-safety"
```

### Querying Decisions

```bash
# Ask for recommendation
muse query "Should I use Redux or Context API here?"
```

**Response**:
```
📊 Based on 47 similar decisions in your git history:

Recommendation: Context API
Confidence: 87%

Reasoning:
  - Files <100 lines: You chose Context (92% of cases)
  - Cross-component state: You chose Redux (Article IV: explicit state)
  - Performance critical: You chose Zustand (2 cases, both successful)

Precedent:
  - src/components/UserProfile.tsx:23 (PR #47, similar complexity)
  - src/hooks/useAuth.tsx:12 (commit abc123, same pattern)
  - Dissent: src/store/cart.ts (chose Redux, but file >200 lines)

Constitutional Basis:
  - Article IV: Continuous learning from past success
  - Pattern: "Simple state → Context, Complex state → Redux"
  - Adopted: 2024-03-15 (commit def456)
```

### Finding Precedent

```bash
# Find similar past decisions
muse precedent --similar "error handling strategy"
```

**Response**:
```
📚 3 relevant precedents found:

1. Result<T,E> Pattern Adoption (confidence: 0.95)
   Date: 2024-02-10
   Commit: abc123
   Description: Replaced try/catch with Result pattern
   Impact: 47 functions refactored
   Outcome: Success (0 regressions, clearer error handling)
   Citation: "See commit abc123 - Result pattern eliminates unclear error states"

2. Custom Error Types (confidence: 0.82)
   Date: 2024-03-01
   PR: #89
   Description: Created typed error hierarchy
   Impact: 12 new error classes
   Outcome: Success (better error messages, easier debugging)
   Citation: "PR #89 - Typed errors reduce debugging time by 40%"

3. Error Boundary Pattern (confidence: 0.71)
   Date: 2024-04-15
   Commit: def456
   Description: React error boundaries for UI failures
   Impact: 5 components wrapped
   Outcome: Mixed (better UX, but added boilerplate)
   Citation: "Commit def456 - Error boundaries prevent white screens"
```

### Evolution Timeline

```bash
# Visualize how style evolved
muse evolution --topic "type-safety"
```

**Output** (ASCII timeline):
```
Type Safety Evolution Timeline

2023-12-01 ─────────────────────────────────────────────────────
  Initial state: 47% Dict[Any,Any] usage

2024-01-15 ─────┬──────────────────────────────────────────────
                │ Commit abc123: First Pydantic model introduced
                └─> Confidence: 0.3 (exploratory)

2024-02-20 ─────┬──────────────────────────────────────────────
                │ PR #34: Converted 12 endpoints to Pydantic
                └─> Confidence: 0.6 (pattern emerging)

2024-03-10 ─────┬──────────────────────────────────────────────
                │ Commit def456: "No Dict[Any,Any]" rule added
                └─> Confidence: 0.85 (established pattern)

2024-04-01 ─────┬──────────────────────────────────────────────
                │ PR #67: Eliminated last 3 Dict[Any,Any]
                └─> Confidence: 0.95 (enforced standard)

2024-10-04 ─────────────────────────────────────────────────────
  Current state: 0% Dict[Any,Any] (100% Pydantic models)

Pattern: Gradual adoption → Team convention → Enforced standard
```

---

## Generated Constitution Format

**constitution.yaml** (auto-generated from git history):

```yaml
# Living Constitution - Auto-Generated from Git History
# Project: my-awesome-project
# Distilled: 2024-10-04
# Commits analyzed: 1,247
# Confidence threshold: 0.7

meta:
  project_name: "my-awesome-project"
  distilled_at: "2024-10-04T12:00:00Z"
  commits_analyzed: 1247
  patterns_extracted: 90
  min_confidence: 0.7

articles:
  type_safety:
    title: "Strict Type Safety"
    confidence: 0.95
    adopted: "2024-03-10"
    rules:
      - "Use Pydantic models instead of Dict[Any,Any]"
      - "All functions must have type annotations"
      - "Avoid 'any' type in TypeScript"
    precedent:
      - commit: "def456"
        description: "Eliminated last Dict[Any,Any] violations"
        impact: "Zero type errors in production"
    violations_detected: 0
    last_violation: "2024-03-09"

  error_handling:
    title: "Result Pattern for Error Handling"
    confidence: 0.89
    adopted: "2024-02-10"
    rules:
      - "Use Result<T,E> pattern instead of try/catch for control flow"
      - "Create typed error classes for domain errors"
      - "React error boundaries for UI failures"
    precedent:
      - commit: "abc123"
        description: "Refactored 47 functions to Result pattern"
        impact: "Clearer error handling, easier testing"
    violations_detected: 2
    last_violation: "2024-09-15"

  testing:
    title: "Test-Driven Development"
    confidence: 0.88
    adopted: "2023-11-01"
    rules:
      - "Write tests before implementation"
      - "AAA pattern (Arrange-Act-Assert)"
      - "100% test success required before merge"
    precedent:
      - pr: 12
        description: "Introduced TDD workflow"
        impact: "Reduced bugs by 60%"
    violations_detected: 5
    last_violation: "2024-10-01"

  architecture:
    title: "State Management Strategy"
    confidence: 0.87
    adopted: "2024-03-15"
    rules:
      - "Simple state (<100 lines): Context API"
      - "Complex state (>100 lines): Redux"
      - "Performance critical: Zustand"
    precedent:
      - pr: 47
        description: "UserProfile refactor - Context API chosen"
        impact: "Reduced boilerplate by 40%"
      - pr: 89
        description: "Cart refactor - Redux chosen for complex state"
        impact: "Better state debugging"
    violations_detected: 1
    last_violation: "2024-08-20"

evolution:
  - date: "2023-11-01"
    event: "TDD workflow adopted"
    confidence_before: 0.2
    confidence_after: 0.6
  - date: "2024-02-10"
    event: "Result pattern adopted"
    confidence_before: 0.3
    confidence_after: 0.8
  - date: "2024-03-10"
    event: "Dict[Any,Any] eliminated"
    confidence_before: 0.6
    confidence_after: 0.95
```

---

## Technical Design

### Component 1: Git History Parser

**Purpose**: Extract decisions from git log, PRs, code reviews

**Implementation**:
```python
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class GitDecision:
    """A single decision extracted from git history."""
    commit_sha: str
    author: str
    date: datetime
    message: str
    files_changed: List[str]
    diff_summary: str
    category: str  # "architecture", "types", "tests", "error_handling"
    pattern: str  # Extracted pattern description
    confidence: float  # 0.0-1.0

class GitHistoryParser:
    """Parse git history to extract architectural decisions."""

    def parse_repository(self, repo_path: str, since: str = None) -> List[GitDecision]:
        """
        Parse git repository for decisions.

        Args:
            repo_path: Path to git repository
            since: Only analyze commits after this date (ISO format)

        Returns:
            List of extracted decisions
        """
        # Use gitpython library
        import git

        repo = git.Repo(repo_path)
        commits = repo.iter_commits(since=since) if since else repo.iter_commits()

        decisions = []
        for commit in commits:
            # Extract decision from commit
            decision = self._extract_decision(commit)
            if decision:
                decisions.append(decision)

        return decisions

    def _extract_decision(self, commit) -> GitDecision | None:
        """Extract architectural decision from single commit."""
        # Pattern matching on commit message and diff
        # Examples:
        # - "Refactor: Replace Dict[Any] with Pydantic" → type_safety
        # - "Add Result pattern to error handling" → error_handling
        # - "Implement TDD for new feature" → testing
        pass
```

### Component 2: Pattern Extractor

**Purpose**: Identify recurring patterns from decisions

**Implementation**:
```python
from typing import List, Dict
from collections import Counter, defaultdict

@dataclass
class Pattern:
    """An identified coding pattern."""
    category: str
    description: str
    confidence: float
    frequency: int
    first_seen: datetime
    last_seen: datetime
    precedents: List[str]  # Commit SHAs or PR numbers

class PatternExtractor:
    """Extract recurring patterns from git decisions."""

    def extract_patterns(
        self,
        decisions: List[GitDecision],
        min_frequency: int = 3,
        min_confidence: float = 0.7
    ) -> List[Pattern]:
        """
        Extract patterns from decisions.

        Args:
            decisions: List of git decisions
            min_frequency: Minimum occurrences to be a pattern
            min_confidence: Minimum confidence score

        Returns:
            List of identified patterns
        """
        # Group by category
        by_category = defaultdict(list)
        for decision in decisions:
            by_category[decision.category].append(decision)

        patterns = []
        for category, cat_decisions in by_category.items():
            # Cluster similar decisions
            clusters = self._cluster_decisions(cat_decisions)

            for cluster in clusters:
                if len(cluster) >= min_frequency:
                    pattern = self._create_pattern(cluster, category)
                    if pattern.confidence >= min_confidence:
                        patterns.append(pattern)

        return patterns

    def _cluster_decisions(self, decisions: List[GitDecision]) -> List[List[GitDecision]]:
        """Cluster similar decisions using semantic similarity."""
        # Use sentence-transformers for semantic clustering
        from sentence_transformers import SentenceTransformer
        import numpy as np
        from sklearn.cluster import DBSCAN

        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Embed decision descriptions
        texts = [f"{d.message} {d.pattern}" for d in decisions]
        embeddings = model.encode(texts)

        # Cluster
        clustering = DBSCAN(eps=0.3, min_samples=2).fit(embeddings)

        # Group by cluster label
        clusters = defaultdict(list)
        for i, label in enumerate(clustering.labels_):
            if label != -1:  # Ignore noise
                clusters[label].append(decisions[i])

        return list(clusters.values())
```

### Component 3: Precedent Database

**Purpose**: Store and query past decisions

**Implementation**:
```python
from agency_memory import EnhancedMemoryStore
from shared.type_definitions import JSONValue

class PrecedentDatabase:
    """Store and query architectural precedents."""

    def __init__(self, store_path: str = "./.muse/precedents.db"):
        self.store = EnhancedMemoryStore(
            db_path=store_path,
            embedding_provider="sentence-transformers"
        )

    def store_pattern(self, pattern: Pattern) -> None:
        """Store pattern as precedent."""
        self.store.store(
            key=f"pattern_{pattern.category}_{pattern.first_seen.isoformat()}",
            content={
                "category": pattern.category,
                "description": pattern.description,
                "confidence": pattern.confidence,
                "frequency": pattern.frequency,
                "precedents": pattern.precedents,
            },
            tags=[pattern.category, "pattern"],
            metadata={
                "first_seen": pattern.first_seen.isoformat(),
                "last_seen": pattern.last_seen.isoformat(),
            }
        )

    def query_similar(self, question: str, category: str = None, limit: int = 3) -> List[Dict[str, JSONValue]]:
        """
        Query for similar precedents.

        Args:
            question: User's question (e.g., "How to handle errors?")
            category: Optional category filter
            limit: Max results

        Returns:
            List of relevant precedents with citations
        """
        # Semantic search via VectorStore
        results = self.store.semantic_search(
            query=question,
            tags=[category] if category else None,
            limit=limit
        )

        return [
            {
                "pattern": r["content"]["description"],
                "confidence": r["content"]["confidence"],
                "precedents": r["content"]["precedents"],
                "category": r["content"]["category"],
            }
            for r in results
        ]
```

### Component 4: CLI Interface

**Purpose**: User-facing commands

**Implementation**:
```python
import click
from pathlib import Path

@click.group()
def cli():
    """Style Distillery - Learn your codebase's DNA"""
    pass

@cli.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.option('--since', default=None, help='Only analyze commits after this date')
@click.option('--min-confidence', default=0.7, help='Minimum pattern confidence')
@click.option('--output', default='./project-dna', help='Output directory')
def distill(repo_path, since, min_confidence, output):
    """Distill coding style from git repository."""
    click.echo(f"🔍 Analyzing git history at {repo_path}...")

    # Parse git history
    parser = GitHistoryParser()
    decisions = parser.parse_repository(repo_path, since=since)
    click.echo(f"   - {len(decisions)} commits analyzed")

    # Extract patterns
    extractor = PatternExtractor()
    patterns = extractor.extract_patterns(decisions, min_confidence=min_confidence)
    click.echo(f"   - {len(patterns)} patterns extracted")

    # Store in precedent database
    db = PrecedentDatabase(f"{output}/precedents.db")
    for pattern in patterns:
        db.store_pattern(pattern)

    # Generate constitution
    generator = ConstitutionGenerator()
    constitution = generator.generate(patterns, decisions)

    # Write outputs
    Path(output).mkdir(parents=True, exist_ok=True)
    with open(f"{output}/constitution.yaml", 'w') as f:
        yaml.dump(constitution, f)

    click.echo(f"✅ Style distilled to: {output}")

@cli.command()
@click.argument('question')
@click.option('--db', default='./project-dna/precedents.db', help='Precedent database path')
def query(question, db):
    """Query for architectural recommendations."""
    precedent_db = PrecedentDatabase(db)
    results = precedent_db.query_similar(question, limit=3)

    if not results:
        click.echo("❌ No relevant precedents found")
        return

    click.echo(f"📊 Based on your git history:\n")
    for i, result in enumerate(results, 1):
        click.echo(f"{i}. {result['pattern']}")
        click.echo(f"   Confidence: {result['confidence']:.2%}")
        click.echo(f"   Precedents: {', '.join(result['precedents'][:3])}")
        click.echo()

@cli.command()
@click.option('--similar', required=True, help='Find precedents similar to this topic')
@click.option('--db', default='./project-dna/precedents.db', help='Precedent database path')
def precedent(similar, db):
    """Find similar past decisions."""
    # Same as query but with more detail
    pass

@cli.command()
@click.option('--topic', required=True, help='Topic to visualize evolution')
@click.option('--db', default='./project-dna/precedents.db', help='Precedent database path')
def evolution(topic, db):
    """Visualize how coding style evolved over time."""
    # Timeline visualization
    pass

if __name__ == '__main__':
    cli()
```

---

## Acceptance Criteria

### AC-1: One-Command Distillation
- **Given**: A git repository with 100+ commits
- **When**: User runs `muse distill /path/to/repo`
- **Then**:
  - Git history parsed successfully
  - Patterns extracted with confidence scores
  - `constitution.yaml` generated
  - Precedent database initialized
  - Process completes in <5 minutes for 1000 commits

### AC-2: Precedent Query
- **Given**: Distilled repository
- **When**: User runs `muse query "How to handle errors?"`
- **Then**:
  - Returns 1-3 relevant precedents
  - Each with confidence score, citations, reasoning
  - Recommendations match actual git history
  - Response time <2 seconds

### AC-3: Constitution Generation
- **Given**: Extracted patterns
- **When**: Constitution generator runs
- **Then**:
  - `constitution.yaml` contains 4+ articles
  - Each article has confidence ≥0.7
  - Precedent citations included (commit SHA/PR number)
  - Evolution timeline generated

### AC-4: External Repo Compatibility
- **Given**: Any public git repository
- **When**: User runs `muse distill`
- **Then**:
  - Works without modifying target repo
  - No dependencies injected into target
  - Outputs stored in separate directory
  - Target repo remains unchanged

### AC-5: Evolution Visualization
- **Given**: Distilled repository
- **When**: User runs `muse evolution --topic "type-safety"`
- **Then**:
  - ASCII timeline displayed
  - Shows confidence evolution over time
  - Lists key commits/PRs
  - Identifies adoption date

---

## Technical Requirements

### Dependencies

```
# Core
gitpython>=3.1.0           # Git history parsing
sentence-transformers>=2.2.0  # Pattern clustering
pydantic>=2.0.0            # Data models
PyYAML>=6.0                # Constitution generation
click>=8.0.0               # CLI interface

# Agency Memory Integration
agency-memory>=0.9.0       # VectorStore (reuse existing)

# Optional
pygments>=2.0.0            # Code syntax highlighting
rich>=13.0.0               # Pretty CLI output
matplotlib>=3.7.0          # Evolution graphs (future)
```

### File Structure

```
style-distillery/
├── style_distillery/
│   ├── __init__.py
│   ├── cli.py                    # Click CLI
│   ├── git_parser.py             # GitHistoryParser
│   ├── pattern_extractor.py     # PatternExtractor
│   ├── precedent_db.py           # PrecedentDatabase
│   ├── constitution_generator.py # ConstitutionGenerator
│   └── models.py                 # Pydantic models
├── tests/
│   ├── test_git_parser.py
│   ├── test_pattern_extractor.py
│   ├── test_precedent_db.py
│   └── fixtures/
│       └── sample_repo/          # Test git repo
├── examples/
│   ├── example_constitution.yaml
│   └── example_queries.sh
├── setup.py
├── README.md
└── LICENSE
```

---

## Risks and Mitigations

### Risk 1: Git History Too Large
- **Impact**: Slow parsing, high memory usage
- **Probability**: High (repos with 10k+ commits)
- **Mitigation**:
  - Stream commits instead of loading all
  - `--since` flag to limit analysis window
  - Pagination for large diffs

### Risk 2: Pattern Extraction Quality
- **Impact**: Low confidence, irrelevant patterns
- **Probability**: Medium (depends on commit quality)
- **Mitigation**:
  - Min frequency threshold (≥3 occurrences)
  - Min confidence threshold (≥0.7)
  - Manual review mode: `muse distill --review`

### Risk 3: Private Repo Access
- **Impact**: Cannot parse repos without git access
- **Probability**: Low (user has local clone)
- **Mitigation**:
  - Works on local clones (no GitHub API needed)
  - Optional GitHub API for PR/review data
  - `gh` CLI integration for authenticated access

### Risk 4: Noisy Commit Messages
- **Impact**: Poor pattern extraction
- **Probability**: High (inconsistent commit styles)
- **Mitigation**:
  - Focus on file diffs, not just messages
  - Use semantic clustering (tolerates noise)
  - Allow custom pattern definitions

---

## Future Enhancements

### Phase 2: Real-Time Monitoring
- Watch repo for new commits
- Update constitution automatically
- Alert on pattern violations

### Phase 3: Team Collaboration
- Multi-user precedent database (shared VectorStore)
- Team consensus patterns (>1 author required)
- Conflict resolution when patterns diverge

### Phase 4: IDE Integration
- VSCode extension: inline precedent suggestions
- Pre-commit hook: "This violates team pattern X"
- GitHub Action: constitutional compliance checks

---

## Success Metrics

- **Distillation Speed**: <5 min for 1000 commits
- **Pattern Quality**: ≥80% of extracted patterns rated "useful" by users
- **Query Accuracy**: ≥90% of recommendations match actual past decisions
- **Adoption**: 100+ repos distilled in first month (after release)

---

**Status**: Draft
**Next Step**: Build Precedent Engine v0.1 (foundation for Style Distillery)
**Review**: ChiefArchitect approval required

---

**This is Gemini's "Style Distillery" vision made concrete.**

Point it at any repo → Learn its DNA → Generate living constitution → Query for decisions → Get recommendations based on YOUR history, not generic best practices.

**Not rules. Taste.**
