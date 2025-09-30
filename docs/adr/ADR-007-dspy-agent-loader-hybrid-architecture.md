# ADR-007: DSPy Agent Loader - Hybrid Architecture for Dual Implementations

Date: 2025-09-30

Status: Accepted

## Context

The Agency framework has 10 core agents originally defined as markdown-only specifications. Five agents (auditor, code_agent, learning_agent, planner, toolsmith) now have experimental DSPy implementations alongside traditional Python implementations.

**Current State:**
- Agent definitions: `.claude/agents/*.md` (markdown specifications)
- Traditional implementations: `src/agency/agents/*.py`
- DSPy implementations: `src/agency/agents/dspy/*.py`
- No unified loader to select between implementations
- No fallback mechanism when DSPy fails
- No performance comparison capability

**Constitutional Requirements:**
- **Article I**: Complete context before action - loader must verify DSPy availability
- **Article II**: 100% verification - fallback ensures system always functions
- **Article IV**: Continuous learning - performance telemetry enables improvement
- **Article V**: Spec-driven development - markdown remains source of truth

## Decision

Implement a **hybrid agent loader architecture** that:

1. **Parses frontmatter** from `.claude/agents/*.md` files containing:
   ```yaml
   implementation:
     traditional: "src/agency/agents/agent_name.py"
     dspy: "src/agency/agents/dspy/agent_name.py"
     preferred: dspy
     features:
       dspy: [list of capabilities]
       traditional: [list of capabilities]
   rollout:
     status: gradual
     fallback: traditional
     comparison: enabled
   ```

2. **Instantiates correct implementation** based on:
   - Preference specified in frontmatter
   - DSPy availability check
   - Runtime configuration overrides
   - Fallback to traditional if DSPy fails

3. **Provides telemetry hooks** for:
   - Performance comparison (DSPy vs traditional)
   - Failure rate tracking
   - Latency measurements
   - Quality metrics collection

4. **Maintains markdown as source of truth**:
   - Agent behavior defined in markdown body
   - Loader augments with programmatic capabilities
   - No loss of self-awareness or version control benefits

## Implementation

Create `src/agency/agents/loader.py` with:

```python
class AgentLoader:
    """Loads agents from markdown with dual implementation support."""
    
    def load_agent(self, agent_path: str, force_implementation: Optional[str] = None) -> Agent:
        """
        Load agent with preferred implementation and fallback.
        
        Args:
            agent_path: Path to .claude/agents/*.md file
            force_implementation: Override to use 'dspy' or 'traditional'
            
        Returns:
            Instantiated agent with telemetry hooks
        """
        # Parse frontmatter
        frontmatter = self._parse_frontmatter(agent_path)
        markdown_spec = self._parse_body(agent_path)
        
        # Determine implementation
        impl_type = force_implementation or frontmatter.implementation.preferred
        
        # Load implementation with fallback
        try:
            if impl_type == "dspy" and self._check_dspy_available():
                agent = self._load_dspy_agent(
                    frontmatter.implementation.dspy,
                    markdown_spec
                )
            else:
                agent = self._load_traditional_agent(
                    frontmatter.implementation.traditional,
                    markdown_spec
                )
        except Exception as e:
            logger.warning(f"Failed to load {impl_type}, falling back: {e}")
            agent = self._load_traditional_agent(
                frontmatter.implementation.traditional,
                markdown_spec
            )
        
        # Wrap with telemetry if comparison enabled
        if frontmatter.rollout.comparison:
            agent = TelemetryWrapper(agent, impl_type)
        
        return agent
```

## Rationale

### Preserves Markdown Benefits
- ✅ Agents remain self-aware (can read their own specs)
- ✅ Version control tracks agent evolution
- ✅ Human-readable specifications
- ✅ No loss of transparency

### Enables Gradual Migration
- ✅ DSPy and traditional coexist safely
- ✅ Per-agent rollout control
- ✅ Easy rollback if issues arise
- ✅ A/B testing capability

### Constitutional Compliance
- ✅ **Article I**: Loader verifies DSPy availability before use
- ✅ **Article II**: Fallback ensures 100% availability
- ✅ **Article IV**: Telemetry enables learning from performance data
- ✅ **Article V**: Markdown specs remain authoritative

### Aligns with ADR-005
- Respects per-agent model policy (`shared/model_policy.py`)
- Loader passes model configuration to agent constructors
- Supports safe defaults and overrides

## Consequences

### Positive
- **Gradual DSPy adoption** without disrupting working system
- **Data-driven decisions** via performance telemetry
- **Safe fallback** maintains system reliability
- **Clear migration path** for remaining 5 agents
- **Self-documenting** via frontmatter metadata

### Negative
- **Additional complexity** managing dual implementations
- **Maintenance burden** keeping both versions aligned
- **Testing requirements** for both implementation paths
- **Deprecation planning** needed for traditional versions

### Mitigation
- Comprehensive integration tests for loader
- Clear deprecation timeline once DSPy proves stable
- Automated alerts when fallback is triggered
- Regular review of telemetry data to inform decisions

## Alternatives Considered

### Alternative 1: Full DSPy Migration (All-In)
**Rejected**: Too risky. No fallback if DSPy has issues. Violates Article II (100% verification).

### Alternative 2: Separate Agent Definitions
**Rejected**: Fragments agent specifications. Loses markdown benefits. Harder to maintain.

### Alternative 3: Runtime Feature Flags Only
**Rejected**: No structured metadata. Harder to track migration status. Poor visibility into capabilities.

### Alternative 4: Keep Markdown-Only (No Loader)
**Rejected**: Doesn't enable programmatic DSPy benefits. Fails Article IV (learning integration).

## Migration Plan

### Phase 1: Loader Implementation (Week 1)
1. ✅ Update frontmatter for 5 DSPy agents (DONE)
2. Build `AgentLoader` class
3. Add frontmatter parser (YAML)
4. Implement DSPy availability check
5. Add telemetry wrapper

### Phase 2: Integration & Testing (Week 1-2)
1. Integration tests for all 5 agents
2. Fallback behavior validation
3. Telemetry collection tests
4. Performance baseline capture

### Phase 3: Production Rollout (Week 2-3)
1. Deploy with DSPy preferred
2. Monitor fallback rate
3. Collect performance metrics
4. Adjust thresholds based on data

### Phase 4: Remaining Agents (Week 3-4)
1. Migrate 5 remaining agents to DSPy
2. Update frontmatter
3. Test and validate
4. Full Agency DSPy coverage

## Success Metrics

- **Loader reliability**: 100% successful instantiation (with fallback)
- **DSPy adoption**: 80%+ of calls use DSPy (20% fallback acceptable)
- **Performance parity**: DSPy latency within 20% of traditional
- **Quality improvement**: DSPy reasoning leads to measurable quality gains
- **Zero downtime**: System never fails due to implementation switching

## Links

- Constitution: `/constitution.md`
- ADR-005: Per-Agent Model Policy
- Agent Frontmatter: `.claude/agents/*.md`
- DSPy Implementations: `src/agency/agents/dspy/`
- Traditional Implementations: `src/agency/agents/`

## Review

- **Weekly**: Check fallback rates and telemetry
- **Monthly**: Evaluate DSPy performance vs traditional
- **Quarterly**: Decide on traditional deprecation timeline