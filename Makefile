# Simple convenience targets for Agency

.PHONY: help verify-soak

help:
	@echo "Available targets:"
	@echo "  verify-soak   Run soak verification and publish to dashboard (requires logs/analysis)"

verify-soak:
	@echo "==> Verifying soak report and publishing to dashboard"
	PERSIST_PATTERNS=true \
	python autonomous_soak_test.py --verify-soak --markdown --channel=dashboard
