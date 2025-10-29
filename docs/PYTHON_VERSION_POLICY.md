# Python Version Policy

**Policy**: AgencyOS uses Python 3.11-3.12 for maximum stability and ML library compatibility.

**Last Updated**: 2025-10-29
**Status**: Active

---

## Current Version

**Required**: Python >= 3.11, < 3.13
**Recommended**: Python 3.12.11 (stable, proven)

---

## Rationale

### Why Not Python 3.13?

**Issue Discovered**: 2025-10-29
- PyTorch 2.9.0 import timeout (30+ seconds) on Python 3.13
- Transformers/sentence-transformers follow PyTorch compatibility
- Python 3.13 released Oct 2024 (too new for ML ecosystem)

**Official Support** (as of Oct 2025):
- PyTorch: Python 3.8-3.12 ✅
- Transformers: Python 3.8-3.12 ✅
- Sentence-transformers: Python 3.8-3.12 ✅

### Why Python 3.12?

**Mars Rover Reliability Principle**:
- ✅ Battle-tested (released Oct 2023, 2+ years of production use)
- ✅ Official ML library support (PyTorch, TensorFlow, transformers)
- ✅ Performance optimizations stable
- ✅ Type system maturity (PEP 695 Generics)

**Not 3.11**:
- 3.12 has better performance (10-15% faster CPython)
- 3.12 has f-string improvements (PEP 701)
- 3.12 is current LTS-equivalent for ML workloads

**Not 3.13**:
- Released Oct 2024 (too new, 0-6 months of production hardening)
- ML libraries lag 6-12 months behind new Python releases
- Import timeouts observed in production testing

---

## Migration Path (When Python 3.13 is Ready)

**Checklist for Future Python 3.13 Adoption**:

1. ✅ PyTorch official support announced (check pytorch.org)
2. ✅ Transformers/HuggingFace compatibility verified
3. ✅ Sentence-transformers import test passes (<5s)
4. ✅ All 1,762+ tests pass on Python 3.13
5. ✅ Benchmark performance comparable or better
6. ✅ Production validation on M4 MAX (128GB test)

**Estimated Timeline**: Q2 2026 (6-12 months after PyTorch 3.13 support)

---

## Environment Setup (Current)

### For Developers

```bash
# Install Python 3.12 (macOS)
brew install python@3.12

# Create venv with correct Python
uv venv --python 3.12
# OR
python3.12 -m venv .venv

# Verify version
python --version  # Should show 3.12.x
```

### For CI/CD

```yaml
# .github/workflows/tests.yml
- uses: actions/setup-python@v4
  with:
    python-version: '3.12'
```

### For Docker

```dockerfile
FROM python:3.12-slim
```

---

## Verification

**Test Python version compatibility**:

```bash
# Quick test (should complete in <5 seconds)
python -c "import torch, transformers, sentence_transformers; print('✅ All ML libs import OK')"

# Full benchmark (should pass all tests)
pytest tests/benchmarks/test_performance.py -v
```

---

## References

- **PyTorch Compatibility**: https://pytorch.org/get-started/locally/
- **Transformers Compatibility**: https://huggingface.co/docs/transformers/installation
- **Python Release Schedule**: https://peps.python.org/pep-0602/
- **AgencyOS Issue**: Phase 1a dependency resolution (2025-10-29)

---

**Review Schedule**: Every 6 months (May, November)
**Next Review**: 2026-05-01
