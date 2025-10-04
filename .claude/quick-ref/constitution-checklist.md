# Constitutional Compliance Checklist

**Quick reference for agents before taking action**

## Article I: Complete Context Before Action
- [ ] Do I have complete information? (No timeouts, no partial results)
- [ ] Have ALL tests run to completion?
- [ ] If timeout occurred: Retry with 2x, 3x, up to 10x timeout
- [ ] Zero broken windows (no "temporary" compromises)

## Article II: 100% Verification and Stability
- [ ] Main branch shows 100% test success?
- [ ] CI pipeline is green?
- [ ] Tests verify REAL functionality (not mocks/simulation)?
- [ ] "Delete the Fire First" priority followed?
- [ ] Definition of Done met: Code ✓ Tests ✓ Pass ✓ Review ✓ CI ✓

## Article III: Automated Merge Enforcement
- [ ] Quality gates enforced (no manual overrides)?
- [ ] Pre-commit hook passing?
- [ ] CI/CD validation complete?
- [ ] Branch protection respected?

## Article IV: Continuous Learning
- [ ] VectorStore query performed for relevant patterns?
- [ ] Successful patterns will be stored after completion?
- [ ] Learning integration active (USE_ENHANCED_MEMORY=true)?

## Article V: Spec-Driven Development
- [ ] Complex feature? → spec.md created/approved?
- [ ] spec.md → plan.md transformation complete?
- [ ] plan.md → TodoWrite tasks broken down?
- [ ] Simple task? → Constitutional compliance verified?

---

**NEVER proceed with constitutional violations - they are BLOCKERS**
