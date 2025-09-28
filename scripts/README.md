# Test Infrastructure Scripts

This directory contains comprehensive test infrastructure scripts to strengthen the test system and prevent future collection failures.

## Scripts Overview

### 1. `test_health_check.py` - Test Health Check System
Comprehensive test health checker that validates the test suite integrity.

**Features:**
- ✅ Syntax validation of all test files
- ✅ Import dependency checking
- ✅ Pytest collection validation
- ✅ Test structure and naming convention checks
- ✅ Configuration validation
- ✅ Detailed issue reporting with severity levels

**Usage:**
```bash
python scripts/test_health_check.py
```

**Integration:** Automatically runs as a pre-commit hook to prevent committing broken tests.

### 2. `test_coverage.py` - Test Coverage Analysis
Advanced coverage runner with multiple output formats and low-coverage identification.

**Features:**
- 🧪 Test execution with coverage collection
- 📊 Multiple report formats (HTML, XML, JSON, terminal)
- 📈 Low coverage module identification
- ⚡ Parallel test execution support
- 🎯 Configurable coverage thresholds
- 🌐 HTML report with browser opening

**Usage:**
```bash
# Basic coverage run
python scripts/test_coverage.py

# With custom threshold and HTML report
python scripts/test_coverage.py --min-coverage 85 --html

# Test specific patterns
python scripts/test_coverage.py --test-pattern "test_memory"

# Include slow tests
python scripts/test_coverage.py --include-slow

# Clean old coverage files first
python scripts/test_coverage.py --clean

# Generate report from existing data
python scripts/test_coverage.py --report-only
```

### 3. `test_runner.py` - Unified Test Runner
Comprehensive test runner that combines health checks, coverage, and various test execution modes.

**Features:**
- 🔍 Integrated health checking
- ⚡ Fast test execution (excludes slow/integration tests)
- 🧪 Full test suite execution
- 📊 Coverage-enabled test runs
- 🎯 Pattern-based test selection

**Usage:**
```bash
# Run health check only
python scripts/test_runner.py health

# Run fast tests (unit tests only)
python scripts/test_runner.py fast

# Run all tests
python scripts/test_runner.py all

# Run tests with coverage
python scripts/test_runner.py coverage --html

# Run specific tests with pattern
python scripts/test_runner.py fast --pattern "test_memory"

# Skip health check (for CI/debugging)
python scripts/test_runner.py all --no-health-check
```

## Pre-commit Integration

The test health check is automatically integrated into the pre-commit hooks to prevent committing broken tests:

```yaml
- id: test-health-check
  name: Test Health Check
  entry: python scripts/test_health_check.py
  language: python
  pass_filenames: false
  always_run: true
  stages: [commit]
```

## Report Outputs

### Health Check Reports
- **Console:** Real-time progress and summary
- **File:** `logs/test_health_report.txt` - Detailed report with all issues

### Coverage Reports
- **Console:** Summary statistics and low-coverage modules
- **HTML:** `coverage/html/index.html` - Interactive coverage browser
- **XML:** `coverage/coverage.xml` - Machine-readable coverage data
- **JSON:** `coverage/coverage.json` - Structured coverage data
- **Text:** `coverage/coverage_report.txt` - Human-readable summary

## Error Detection

The health check system detects:
- ❌ **Syntax errors** in test files
- ❌ **Missing dependencies** (pytest, pytest-asyncio, etc.)
- ❌ **Import failures** in test modules
- ❌ **Collection failures** during pytest discovery
- ⚠️ **Configuration issues** (missing pytest.ini, markers)
- ⚠️ **Naming convention violations**
- ⚠️ **Empty test files**

## Best Practices

1. **Run health check before committing:**
   ```bash
   python scripts/test_runner.py health
   ```

2. **Monitor coverage regularly:**
   ```bash
   python scripts/test_runner.py coverage --html
   ```

3. **Use fast tests during development:**
   ```bash
   python scripts/test_runner.py fast --pattern "your_feature"
   ```

4. **Full validation before releases:**
   ```bash
   python scripts/test_runner.py all
   python scripts/test_coverage.py --min-coverage 85
   ```

## Exit Codes

All scripts follow standard exit code conventions:
- `0` - Success
- `1` - Failure/errors found
- `130` - Interrupted by user (Ctrl+C)

## Dependencies

Required packages for full functionality:
- `pytest` - Core testing framework
- `pytest-cov` - Coverage integration
- `pytest-asyncio` - Async test support
- `pytest-xdist` - Parallel execution (optional)
- `pytest-mock` - Mocking utilities (optional)

## Troubleshooting

### Health Check Issues
- **Syntax errors:** Fix the reported syntax issues in test files
- **Import errors:** Ensure all required modules are installed and accessible
- **Collection failures:** Check for conflicting test configurations or broken imports

### Coverage Issues
- **Low coverage:** Review the low-coverage report and add tests for uncovered modules
- **Collection timeouts:** Consider breaking up large test suites or improving test performance
- **Missing reports:** Ensure coverage dependencies are installed

For more specific issues, check the detailed reports generated in the `logs/` and `coverage/` directories.