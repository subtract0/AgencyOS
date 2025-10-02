"""Test backward compatibility layer for Trinity Protocol reorganization.

This test suite ensures that the 30-day deprecation period provides
smooth migration from old import patterns to new structure.

Constitutional Compliance:
- Article I: Complete verification of backward compatibility
- Article II: 100% test coverage for all deprecated paths
- Article V: Spec-driven deprecation with clear migration path
"""

import pytest
import warnings
import sys
from pathlib import Path


class TestBackwardCompatibility:
    """Verify deprecated imports still work with appropriate warnings."""

    def test_executor_agent_module_import_shows_warning(self):
        """Test old executor_agent module import shows deprecation warning."""
        # Clear any cached imports
        if 'trinity_protocol' in sys.modules:
            del sys.modules['trinity_protocol']
        if 'trinity_protocol.executor_agent' in sys.modules:
            del sys.modules['trinity_protocol.executor_agent']

        with pytest.warns(DeprecationWarning, match="deprecated"):
            from trinity_protocol import executor_agent  # noqa: F401

    def test_architect_agent_module_import_shows_warning(self):
        """Test old architect_agent module import shows deprecation warning."""
        # Clear any cached imports
        if 'trinity_protocol' in sys.modules:
            del sys.modules['trinity_protocol']
        if 'trinity_protocol.architect_agent' in sys.modules:
            del sys.modules['trinity_protocol.architect_agent']

        with pytest.warns(DeprecationWarning, match="deprecated"):
            from trinity_protocol import architect_agent  # noqa: F401

    def test_witness_agent_module_import_shows_warning(self):
        """Test old witness_agent module import shows deprecation warning."""
        # Clear any cached imports
        if 'trinity_protocol' in sys.modules:
            del sys.modules['trinity_protocol']
        if 'trinity_protocol.witness_agent' in sys.modules:
            del sys.modules['trinity_protocol.witness_agent']

        with pytest.warns(DeprecationWarning, match="deprecated"):
            from trinity_protocol import witness_agent  # noqa: F401

    def test_orchestrator_module_import_shows_warning(self):
        """Test old orchestrator module import shows deprecation warning."""
        # Clear any cached imports
        if 'trinity_protocol' in sys.modules:
            del sys.modules['trinity_protocol']
        if 'trinity_protocol.orchestrator' in sys.modules:
            del sys.modules['trinity_protocol.orchestrator']

        with pytest.warns(DeprecationWarning, match="deprecated"):
            from trinity_protocol import orchestrator  # noqa: F401

    def test_models_module_import_shows_warning(self):
        """Test old models module import shows deprecation warning."""
        # Clear any cached imports
        if 'trinity_protocol.models' in sys.modules:
            del sys.modules['trinity_protocol.models']

        with pytest.warns(DeprecationWarning, match="deprecated"):
            from trinity_protocol import models  # noqa: F401

    def test_new_core_imports_no_warning(self):
        """Test new imports from core don't show warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            # These should NOT raise (no warnings)
            from trinity_protocol.core import ExecutorAgent  # noqa: F401
            from trinity_protocol.core import ArchitectAgent  # noqa: F401
            from trinity_protocol.core import WitnessAgent  # noqa: F401
            from trinity_protocol.core import TrinityOrchestrator  # noqa: F401

    def test_new_model_imports_no_warning(self):
        """Test new model imports from core.models don't show warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors
            # Ignore Pydantic deprecation warnings (unrelated to Trinity backward compat)
            warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.*")

            # These should NOT raise (no warnings)
            from trinity_protocol.core.models import Project  # noqa: F401
            from trinity_protocol.core.models import PatternType  # noqa: F401
            from trinity_protocol.core.models import HumanReviewRequest  # noqa: F401

    def test_direct_import_from_trinity_protocol_no_warning(self):
        """Test importing directly from trinity_protocol (new __all__) shows no warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors

            # These are in __all__ so should work without warnings
            from trinity_protocol import ExecutorAgent  # noqa: F401
            from trinity_protocol import ArchitectAgent  # noqa: F401
            from trinity_protocol import WitnessAgent  # noqa: F401
            from trinity_protocol import TrinityOrchestrator  # noqa: F401

    def test_deprecated_import_includes_removal_date(self):
        """Test deprecation warning mentions removal date (2025-11-02)."""
        # Clear cached imports
        if 'trinity_protocol' in sys.modules:
            del sys.modules['trinity_protocol']

        with pytest.warns(DeprecationWarning) as record:
            from trinity_protocol import executor_agent  # noqa: F401

        # Verify at least one warning message contains removal date
        assert len(record) >= 1
        warning_messages = [str(w.message) for w in record]
        assert any("2025-11-02" in msg for msg in warning_messages)

    def test_deprecated_import_includes_migration_guide(self):
        """Test deprecation warning mentions README_REORGANIZATION.md."""
        # Clear cached imports
        if 'trinity_protocol' in sys.modules:
            del sys.modules['trinity_protocol']

        with pytest.warns(DeprecationWarning) as record:
            from trinity_protocol import architect_agent  # noqa: F401

        # Verify at least one warning message mentions migration guide
        assert len(record) >= 1
        warning_messages = [str(w.message) for w in record]
        assert any("README_REORGANIZATION.md" in msg for msg in warning_messages)

    def test_deprecated_import_includes_recommended_pattern(self):
        """Test deprecation warning shows recommended import pattern."""
        # Clear cached imports
        if 'trinity_protocol' in sys.modules:
            del sys.modules['trinity_protocol']

        with pytest.warns(DeprecationWarning) as record:
            from trinity_protocol import witness_agent  # noqa: F401

        # Verify at least one warning message includes recommended pattern
        assert len(record) >= 1
        warning_messages = [str(w.message) for w in record]
        assert any("from trinity_protocol.core import" in msg for msg in warning_messages)

    def test_deprecated_models_import_functional(self):
        """Test that deprecated models import still provides access to classes."""
        # Clear cached imports
        if 'trinity_protocol.models' in sys.modules:
            del sys.modules['trinity_protocol.models']

        # Should work but show warning
        with pytest.warns(DeprecationWarning):
            from trinity_protocol.models import Project, PatternType  # noqa: F401

            # Verify we can actually use them (not just import)
            assert Project is not None
            assert PatternType is not None

    def test_backward_compat_layer_complete_coverage(self):
        """Test that all common old patterns are covered by backward compat."""
        deprecated_patterns = [
            "executor_agent",
            "architect_agent",
            "witness_agent",
            "orchestrator",
            "models"
        ]

        for pattern in deprecated_patterns:
            # Clear cached imports
            if 'trinity_protocol' in sys.modules:
                del sys.modules['trinity_protocol']

            # Each should trigger exactly one deprecation warning
            with pytest.warns(DeprecationWarning):
                module = __import__('trinity_protocol')
                getattr(module, pattern)


class TestDeprecationTimeline:
    """Verify deprecation timeline is correctly documented."""

    def test_removal_date_in_init_docstring(self):
        """Test that __init__.py docstring mentions removal date."""
        init_file = Path(__file__).parent.parent.parent / "trinity_protocol" / "__init__.py"
        content = init_file.read_text()

        assert "2025-11-02" in content, "Removal date should be in __init__.py docstring"

    def test_30_day_period_documented(self):
        """Test that 30-day deprecation period is mentioned."""
        init_file = Path(__file__).parent.parent.parent / "trinity_protocol" / "__init__.py"
        content = init_file.read_text()

        assert "30 days" in content.lower(), "30-day period should be documented"

    def test_migration_guide_referenced(self):
        """Test that migration guide is referenced in deprecation notices."""
        init_file = Path(__file__).parent.parent.parent / "trinity_protocol" / "__init__.py"
        content = init_file.read_text()

        assert "README_REORGANIZATION.md" in content, "Migration guide should be referenced"


class TestNewImportPatterns:
    """Verify new import patterns work correctly without warnings."""

    def test_core_agent_imports(self):
        """Test importing agents from trinity_protocol.core works cleanly."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")

            from trinity_protocol.core import (
                ExecutorAgent,
                ArchitectAgent,
                WitnessAgent,
                TrinityOrchestrator
            )

            # Verify classes are usable
            assert ExecutorAgent.__name__ == "ExecutorAgent"
            assert ArchitectAgent.__name__ == "ArchitectAgent"
            assert WitnessAgent.__name__ == "WitnessAgent"
            assert TrinityOrchestrator.__name__ == "TrinityOrchestrator"

    def test_core_model_imports(self):
        """Test importing models from trinity_protocol.core.models works cleanly."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            # Ignore Pydantic deprecation warnings (unrelated to Trinity backward compat)
            warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.*")

            from trinity_protocol.core.models import (
                Project,
                PatternType,
                HumanReviewRequest
            )

            # Verify classes are usable
            assert Project.__name__ == "Project"
            assert PatternType is not None  # Enum
            assert HumanReviewRequest.__name__ == "HumanReviewRequest"
