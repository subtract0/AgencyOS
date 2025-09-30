# Agency OS Development Makefile
# Common development tasks and shortcuts

.PHONY: help setup test test-all clean lint verify-soak

# Default target
help:
	@echo "Agency OS Development Commands"
	@echo "=============================="
	@echo "Quick Start:"
	@echo "  make setup          - Complete dev environment setup"
	@echo "  make test           - Run unit tests (fast)"
	@echo "  make test-all       - Run ALL tests (constitutional requirement)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Auto-fix code style issues"
	@echo "  make clean          - Remove temporary files"
	@echo ""
	@echo "Advanced:"
	@echo "  make verify-soak    - Run soak verification and publish"
	@echo ""
	@echo "Constitutional requirement: make test-all must pass 100%"

# Quick setup for new developers
setup:
	@echo "==> Setting up development environment"
	@./setup_dev.sh

# Testing targets (Constitutional Article II: 100% pass rate required)
test:
	@echo "==> Running unit tests"
	@python run_tests.py

test-all:
	@echo "==> Running ALL tests (Constitutional compliance)"
	@python run_tests.py --run-all

# Clean temporary files
clean:
	@echo "==> Cleaning temporary files"
	@find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.bak" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .ruff_cache .mypy_cache 2>/dev/null || true
	@echo "Clean complete ✓"

# Lint and format code
lint:
	@echo "==> Running ruff formatter and fixer"
	@ruff check . --fix
	@ruff format .

# Original verify-soak target
verify-soak:
	@echo "==> Verifying soak report and publishing to dashboard"
	PERSIST_PATTERNS=true \
	python autonomous_soak_test.py --verify-soak --markdown --channel=dashboard
