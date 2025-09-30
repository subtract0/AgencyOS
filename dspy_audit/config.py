"""
Configuration and feature flags for DSPy Audit System

Allows gradual migration from legacy to DSPy-based system.
"""

import os
from typing import Any
from .type_definitions import ConfigDict


class AuditConfig:
    """Configuration manager for audit system."""

    @staticmethod
    def get_feature_flags() -> dict[str, bool]:
        """
        Get feature flags from environment variables.

        Returns:
            Dictionary of feature flags
        """
        return {
            # DSPy Integration
            "use_dspy_audit": os.getenv("USE_DSPY_AUDIT", "false").lower() == "true",
            "use_dspy_optimization": os.getenv("USE_DSPY_OPTIMIZATION", "false").lower()
            == "true",
            "use_dspy_learning": os.getenv("USE_DSPY_LEARNING", "false").lower()
            == "true",
            # Parallel Execution
            "parallel_audit_execution": os.getenv("PARALLEL_AUDIT", "true").lower()
            == "true",
            "max_parallel_audits": int(os.getenv("MAX_PARALLEL_AUDITS", "3")),
            # Learning Integration
            "enable_vectorstore_learning": os.getenv(
                "ENABLE_VECTORSTORE_LEARNING", "true"
            ).lower()
            == "true",
            "store_audit_patterns": os.getenv("STORE_AUDIT_PATTERNS", "true").lower()
            == "true",
            # Verification and Rollback
            "auto_rollback_on_failure": os.getenv("AUTO_ROLLBACK", "true").lower()
            == "true",
            "require_test_verification": os.getenv(
                "REQUIRE_TEST_VERIFICATION", "true"
            ).lower()
            == "true",
            "min_test_coverage": float(os.getenv("MIN_TEST_COVERAGE", "0.8")),
            # Constitutional Compliance
            "enforce_constitutional": os.getenv(
                "ENFORCE_CONSTITUTIONAL", "true"
            ).lower()
            == "true",
            "block_on_violation": os.getenv("BLOCK_ON_VIOLATION", "true").lower()
            == "true",
            # Monitoring and Metrics
            "enable_metrics_tracking": os.getenv("ENABLE_METRICS", "true").lower()
            == "true",
            "enable_telemetry": os.getenv("ENABLE_TELEMETRY", "true").lower() == "true",
            # A/B Testing
            "ab_test_enabled": os.getenv("AB_TEST_AUDIT", "false").lower() == "true",
            "ab_test_percentage": float(
                os.getenv("AB_TEST_PERCENTAGE", "0.1")
            ),  # 10% use new system
            # Debug and Development
            "debug_mode": os.getenv("DEBUG_AUDIT", "false").lower() == "true",
            "dry_run_mode": os.getenv("DRY_RUN_AUDIT", "false").lower() == "true",
        }

    @staticmethod
    def get_audit_config() -> ConfigDict:
        """
        Get complete audit configuration.

        Returns:
            Dictionary of configuration settings
        """
        flags = AuditConfig.get_feature_flags()

        return {
            "feature_flags": flags,
            "prioritization": {
                "weights": {
                    "constitutional": 0.5,
                    "security": 0.3,
                    "coverage": 0.15,
                    "complexity": 0.05,
                },
                "max_fixes_per_session": 5,
                "max_time_per_fix": 10,  # minutes
            },
            "necessary_thresholds": {
                "N": 0.8,  # No missing behaviors
                "E1": 0.7,  # Edge cases
                "C": 0.8,  # Comprehensive
                "E2": 0.7,  # Error conditions
                "S1": 0.9,  # State validation
                "S2": 0.9,  # Side effects
                "A": 0.6,  # Async operations
                "R": 0.8,  # Regression prevention
                "Y": 0.7,  # Yielding confidence
            },
            "quality_targets": {
                "min_qt_score": 0.6,
                "target_qt_score": 0.8,
                "critical_qt_threshold": 0.3,
            },
            "paths": {
                "audit_logs": "logs/audits",
                "model_cache": "models/dspy_cache",
                "training_data": "data/audit_training",
                "vectorstore": "agency_memory/vector_store.py",
            },
            "dspy_settings": {
                "model": os.getenv("DSPY_MODEL", "gpt-4"),
                "temperature": float(os.getenv("DSPY_TEMPERATURE", "0.7")),
                "max_tokens": int(os.getenv("DSPY_MAX_TOKENS", "2048")),
                "num_candidates": int(os.getenv("DSPY_NUM_CANDIDATES", "8")),
                "max_bootstrapped_demos": int(os.getenv("DSPY_MAX_BOOTSTRAP", "4")),
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl": 3600,  # 1 hour
                "max_cache_size": 100,  # MB
                "timeout_seconds": 300,  # 5 minutes
            },
        }

    @staticmethod
    def should_use_dspy() -> bool:
        """
        Determine if DSPy should be used based on flags and conditions.

        Returns:
            True if DSPy should be used
        """
        flags = AuditConfig.get_feature_flags()

        # Check if DSPy is enabled
        if not flags["use_dspy_audit"]:
            return False

        # Check if we're in A/B test
        if flags["ab_test_enabled"]:
            import random

            return random.random() < flags["ab_test_percentage"]

        return True

    @staticmethod
    def get_rollback_strategy() -> str:
        """
        Get the rollback strategy based on configuration.

        Returns:
            Rollback strategy name
        """
        flags = AuditConfig.get_feature_flags()

        if flags["dry_run_mode"]:
            return "none"  # No changes in dry run

        if flags["auto_rollback_on_failure"]:
            return "automatic"

        return "manual"

    @staticmethod
    def validate_configuration() -> dict[str, bool]:
        """
        Validate the current configuration for consistency.

        Returns:
            Dictionary of validation results
        """
        config = AuditConfig.get_audit_config()
        flags = config["feature_flags"]
        validations = {}

        # Check DSPy dependencies
        if flags["use_dspy_audit"]:
            try:
                import dspy

                validations["dspy_available"] = True
            except ImportError:
                validations["dspy_available"] = False
                validations["error"] = "DSPy enabled but not installed"

        # Check learning dependencies
        if flags["enable_vectorstore_learning"]:
            from pathlib import Path

            vectorstore_path = Path(config["paths"]["vectorstore"])
            validations["vectorstore_exists"] = vectorstore_path.exists()

        # Check necessary thresholds
        thresholds = config["necessary_thresholds"]
        validations["thresholds_valid"] = all(
            0.0 <= v <= 1.0 for v in thresholds.values()
        )

        # Check paths
        from pathlib import Path

        for path_name, path_value in config["paths"].items():
            path = Path(path_value)
            if path_name != "vectorstore":  # Special case
                validations[f"path_{path_name}_exists"] = path.parent.exists()

        return validations


# Singleton instance
audit_config = AuditConfig()


def get_config() -> ConfigDict:
    """Get the audit configuration."""
    return audit_config.get_audit_config()


def get_flags() -> dict[str, bool]:
    """Get feature flags."""
    return audit_config.get_feature_flags()


def should_use_dspy() -> bool:
    """Check if DSPy should be used."""
    return audit_config.should_use_dspy()


def validate_config() -> dict[str, bool]:
    """Validate configuration."""
    return audit_config.validate_configuration()
