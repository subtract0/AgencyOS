"""
Migration validation tests for PR #28: SpaceX-style De-bloating.
Ensures smooth migration from deprecated modules to new implementations.
"""

import pytest
import sys
import os
from pathlib import Path
from typing import Any

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMemoryMigration:
    """Test memory system migration from memory_v2 to agency_memory."""

    def test_enhanced_memory_store_accessible(self):
        """Test that EnhancedMemoryStore is accessible from new location."""
        from agency_memory.enhanced_memory_store import EnhancedMemoryStore

        # Should be able to instantiate
        store = EnhancedMemoryStore()
        assert store is not None
        assert hasattr(store, 'store_memory')
        assert hasattr(store, 'get_memory')
        assert hasattr(store, 'search_memories')

    def test_swarm_memory_preserved(self):
        """Test that SwarmMemory remains available for agent features."""
        from agency_memory.swarm_memory import SwarmMemory

        # Should be able to instantiate with agent_id
        memory = SwarmMemory(agent_id="test_agent")
        assert memory is not None
        assert memory.agent_id == "test_agent"
        assert hasattr(memory, 'store')
        assert hasattr(memory, 'search')

    def test_memory_v2_removed(self):
        """Test that memory_v2 module is completely removed."""
        # memory_v2.py should not exist
        assert not Path("memory_v2.py").exists()

        # Should not be importable
        with pytest.raises(ImportError):
            import memory_v2  # noqa: F401

    def test_no_dangling_memory_v2_imports(self):
        """Test that no Python files contain memory_v2 imports."""
        python_files = Path(".").rglob("*.py")
        problematic_files = []

        for py_file in python_files:
            if ".venv" in str(py_file) or "__pycache__" in str(py_file) or "test_migration_validation.py" in str(py_file) or "validate_migration.py" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                # Check for actual imports, not comments
                for line in content.split('\n'):
                    if ('from memory_v2' in line or 'import memory_v2' in line) and not line.strip().startswith('#'):
                        problematic_files.append(str(py_file))
                        break
            except Exception:
                pass  # Skip files we can't read

        assert len(problematic_files) == 0, f"Files still importing memory_v2: {problematic_files}"


class TestPatternMigration:
    """Test pattern system migration to unified pattern_intelligence."""

    def test_pattern_intelligence_accessible(self):
        """Test that pattern_intelligence module is functional."""
        from pattern_intelligence import CodingPattern
        from pattern_intelligence.pattern_store import PatternStore

        # Should be able to create instances
        store = PatternStore()
        assert store is not None
        assert hasattr(store, 'store_pattern')
        assert hasattr(store, 'find_patterns')

        # CodingPattern should be importable
        assert CodingPattern is not None

    def test_core_patterns_removed(self):
        """Test that core/patterns.py is completely removed."""
        # core/patterns.py should not exist
        assert not Path("core/patterns.py").exists()

        # Should not be importable
        with pytest.raises(ImportError):
            from core.patterns import Pattern  # noqa: F401

    def test_migration_module_removed(self):
        """Test that pattern_intelligence/migration.py is removed."""
        assert not Path("pattern_intelligence/migration.py").exists()

        with pytest.raises(ImportError):
            from pattern_intelligence.migration import migrate_pattern  # noqa: F401

    def test_no_dangling_pattern_imports(self):
        """Test that no Python files contain old pattern imports."""
        python_files = Path(".").rglob("*.py")
        problematic_files = []

        deprecated_imports = [
            'from core.patterns import',
            'import core.patterns'
        ]

        for py_file in python_files:
            if ".venv" in str(py_file) or "__pycache__" in str(py_file) or "test_migration" in str(py_file) or "validate_migration" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for line in content.split('\n'):
                    if not line.strip().startswith('#'):
                        for deprecated in deprecated_imports:
                            if deprecated in line:
                                problematic_files.append(str(py_file))
                                break
            except Exception:
                pass

        assert len(problematic_files) == 0, f"Files still using old pattern imports: {problematic_files}"


class TestRemovedModules:
    """Test that all intended removals are complete."""

    def test_unified_edit_removed(self):
        """Test that core/unified_edit.py is removed."""
        assert not Path("core/unified_edit.py").exists()

    def test_demos_archive_removed(self):
        """Test that demos/archive directory is removed."""
        assert not Path("demos/archive").exists()

    def test_examples_directory_removed(self):
        """Test that examples directory is removed."""
        assert not Path("examples").exists()

    def test_subagent_example_removed(self):
        """Test that subagent_example directory is removed."""
        assert not Path("subagent_example").exists()


class TestBackwardCompatibility:
    """Test backward compatibility features during migration period."""

    def test_unified_core_provides_compatibility(self):
        """Test that UnifiedCore provides backward-compatible methods."""
        from core import UnifiedCore

        core = UnifiedCore()

        # Should have backward-compatible methods
        assert hasattr(core, 'detect_errors')
        assert hasattr(core, 'fix_errors')
        assert hasattr(core, 'verify_fix')
        assert hasattr(core, 'learn_pattern')
        assert hasattr(core, 'find_patterns')

    def test_learn_pattern_migration_message(self):
        """Test that learn_pattern provides clear migration guidance."""
        from core import UnifiedCore

        # Without pattern store, should raise NotImplementedError with migration message
        core = UnifiedCore()
        core.pattern_store = None  # Ensure no pattern store

        with pytest.raises(NotImplementedError) as exc_info:
            core.learn_pattern("TestError", "old_code", "new_code", True)

        assert "Migration:" in str(exc_info.value)
        assert "pattern_intelligence" in str(exc_info.value)


class TestMigrationDocumentation:
    """Test that migration documentation exists and is complete."""

    def test_migration_md_exists(self):
        """Test that MIGRATION.md exists and contains required sections."""
        migration_file = Path("MIGRATION.md")
        assert migration_file.exists(), "MIGRATION.md file is missing"

        content = migration_file.read_text()

        # Check for required sections
        required_sections = [
            "Breaking Changes",
            "Migration Path",
            "Memory System Consolidation",
            "Pattern System Unification",
            "Import Path Changes",
            "Validation Script",
            "Rollback Strategy"
        ]

        for section in required_sections:
            assert section in content, f"MIGRATION.md missing section: {section}"

    def test_validation_script_exists(self):
        """Test that the migration validation script exists."""
        script_path = Path("scripts/validate_migration.py")
        assert script_path.exists(), "Migration validation script is missing"

        # Should be executable Python
        content = script_path.read_text()
        assert "def check_memory_migration" in content
        assert "def check_pattern_migration" in content
        assert "def check_removed_modules" in content


class TestTypeCompatibility:
    """Test Python version compatibility."""

    def test_no_python39_type_hints(self):
        """Test that we use Dict[str, ...] instead of dict[str, ...] for compatibility."""
        core_init = Path("core/__init__.py")
        assert core_init.exists()

        content = core_init.read_text()

        # Check for Python 3.9+ style type hints
        import re
        # Look for lowercase dict, list, tuple used as type hints
        pattern = r':\s*(dict|list|tuple)\['

        matches = re.findall(pattern, content)
        assert len(matches) == 0, f"Found Python 3.9+ type hints: {matches}. Use Dict, List, Tuple from typing instead."


class TestPerformanceOptimization:
    """Test performance considerations mentioned in review."""

    def test_pattern_store_lazy_initialization(self):
        """Test that PatternStore uses lazy initialization."""
        from core import UnifiedCore

        # Create core without pattern store
        os.environ['PERSIST_PATTERNS'] = 'false'
        core = UnifiedCore()

        # Pattern store should not be initialized until needed
        assert core.pattern_store is None or not hasattr(core, '_pattern_store_initialized')

    def test_learning_loop_optional(self):
        """Test that LearningLoop is optional and doesn't break if unavailable."""
        from core import UnifiedCore

        core = UnifiedCore()

        # Should handle missing learning loop gracefully
        if core.learning_loop is None:
            # Should still work without errors
            metrics = core.get_learning_metrics()
            assert metrics == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])