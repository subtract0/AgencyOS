#!/usr/bin/env python3
"""
Trinity Local Orchestrator → HybridExecutor Integration Script

Safely migrates ~/.trinity-local/trinity_protocol/core/orchestrator.py to use the new
HybridExecutor with AgentRegistry and EscalationPolicy.

Features:
- Creates timestamped backup before modifications
- Updates imports and executor spawning logic
- Loads configuration from trinity_hybrid_config.yaml
- Maintains backward compatibility
- Comprehensive error handling and rollback
- Detailed logging of all changes

Usage:
    python scripts/integrate_hybrid_executor.py [--dry-run] [--force]

Options:
    --dry-run: Show changes without applying them
    --force: Skip confirmation prompts
"""

import argparse
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class IntegrationError(Exception):
    """Raised when integration fails."""

    pass


class HybridExecutorIntegrator:
    """
    Orchestrator integration manager for HybridExecutor.

    Handles:
    - Backup creation
    - Import updates
    - Executor spawning modification
    - Configuration loading
    - Rollback on failure
    """

    def __init__(
        self,
        trinity_home: str = "~/.trinity-local",
        agency_root: str | None = None,
        dry_run: bool = False,
    ):
        """
        Initialize integrator.

        Args:
            trinity_home: Trinity Local installation directory
            agency_root: Agency OS repository root (auto-detected if None)
            dry_run: If True, show changes without applying
        """
        self.trinity_home = Path(trinity_home).expanduser()
        self.agency_root = Path(agency_root or Path.cwd())
        self.dry_run = dry_run

        # Paths
        self.orchestrator_path = (
            self.trinity_home / "trinity_protocol" / "core" / "orchestrator.py"
        )
        self.backup_dir = self.trinity_home / "backups"
        self.config_path = (
            self.agency_root / "trinity_protocol" / "config" / "trinity_hybrid_config.yaml"
        )

        # State tracking
        self.backup_path: Path | None = None
        self.changes_made = False

    def run(self) -> bool:
        """
        Execute integration workflow.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("Trinity Local → HybridExecutor Integration")
            logger.info("=" * 60)

            # Step 1: Validate environment
            logger.info("Step 1/6: Validating environment...")
            self._validate_environment()

            # Step 2: Create backup
            logger.info("Step 2/6: Creating backup...")
            self._create_backup()

            # Step 3: Update imports
            logger.info("Step 3/6: Updating imports...")
            self._update_imports()

            # Step 4: Update executor spawning
            logger.info("Step 4/6: Updating executor spawning logic...")
            self._update_executor_spawning()

            # Step 5: Add configuration loading
            logger.info("Step 5/6: Adding configuration loading...")
            self._add_config_loading()

            # Step 6: Verify modifications
            logger.info("Step 6/6: Verifying modifications...")
            self._verify_changes()

            if self.dry_run:
                logger.info("✅ DRY RUN: All checks passed. No changes applied.")
            else:
                logger.info("✅ Integration completed successfully!")
                logger.info(f"📋 Backup saved to: {self.backup_path}")
                logger.info(f"📝 Modified file: {self.orchestrator_path}")

            return True

        except IntegrationError as e:
            logger.error(f"❌ Integration failed: {e}")
            if self.changes_made and not self.dry_run:
                logger.info("🔄 Attempting rollback...")
                self._rollback()
            return False

        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            if self.changes_made and not self.dry_run:
                logger.info("🔄 Attempting rollback...")
                self._rollback()
            return False

    def _validate_environment(self) -> None:
        """Validate environment and required files."""
        # Check orchestrator exists
        if not self.orchestrator_path.exists():
            raise IntegrationError(
                f"Orchestrator not found at {self.orchestrator_path}. "
                "Is Trinity Local installed?"
            )

        # Check config exists
        if not self.config_path.exists():
            raise IntegrationError(
                f"Configuration not found at {self.config_path}. "
                f"Run from Agency root: {self.agency_root}"
            )

        # Check for required Agency components
        hybrid_executor_path = (
            self.agency_root / "trinity_protocol" / "core" / "hybrid_executor.py"
        )
        agent_registry_path = (
            self.agency_root / "trinity_protocol" / "core" / "agent_registry.py"
        )

        if not hybrid_executor_path.exists():
            raise IntegrationError(
                f"HybridExecutor not found at {hybrid_executor_path}"
            )

        if not agent_registry_path.exists():
            raise IntegrationError(f"AgentRegistry not found at {agent_registry_path}")

        logger.info(f"✅ Trinity home: {self.trinity_home}")
        logger.info(f"✅ Agency root: {self.agency_root}")
        logger.info(f"✅ Config found: {self.config_path}")

    def _create_backup(self) -> None:
        """Create timestamped backup of current orchestrator."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = self.backup_dir / f"orchestrator_backup_{timestamp}.py"

        if not self.dry_run:
            shutil.copy2(self.orchestrator_path, self.backup_path)
            logger.info(f"✅ Backup created: {self.backup_path}")
        else:
            logger.info(f"✅ Would create backup: {self.backup_path}")

    def _update_imports(self) -> None:
        """Update imports to include HybridExecutor and dependencies."""
        content = self.orchestrator_path.read_text()

        # Check if already integrated
        if "from trinity_protocol.core.hybrid_executor import" in content:
            logger.warning(
                "⚠️  HybridExecutor imports already present. Skipping import update."
            )
            return

        # Find the OllamaClient import line
        import_line = "from trinity_protocol.core.ollama_client import OllamaClient, OllamaError, OllamaTimeout"

        if import_line not in content:
            raise IntegrationError(
                "Could not find OllamaClient import line. File structure may have changed."
            )

        # New imports to add (after OllamaClient import)
        new_imports = """
# HybridExecutor imports (added by integration script)
from trinity_protocol.core.hybrid_executor import (
    HybridExecutor,
    TaskType,
    TaskResult,
    create_hybrid_executor,
)
from trinity_protocol.core.agent_registry import (
    AgentRegistry,
    AgentType,
    ModelTier,
    create_agent_registry,
)
from trinity_protocol.core.escalation_rules import (
    EscalationPolicy,
    create_escalation_policy,
)
from shared.agent_context import AgentContext
from shared.cost_tracker import CostTracker
from shared.message_bus import MessageBus
"""

        # Insert new imports after OllamaClient import
        updated_content = content.replace(
            import_line, import_line + new_imports
        )

        if not self.dry_run:
            self.orchestrator_path.write_text(updated_content)
            self.changes_made = True
            logger.info("✅ Imports updated")
        else:
            logger.info("✅ Would add HybridExecutor imports")

    def _update_executor_spawning(self) -> None:
        """Update _spawn_executor method to use HybridExecutor."""
        content = self.orchestrator_path.read_text()

        # Check if already using HybridExecutor
        if "self.hybrid_executor" in content:
            logger.warning(
                "⚠️  HybridExecutor spawning already present. Skipping executor update."
            )
            return

        # Find the _spawn_executor method - need to find the LINE start, not just the text
        executor_text_pos = content.find("async def _spawn_executor(")
        if executor_text_pos == -1:
            raise IntegrationError("Could not find _spawn_executor method")

        # Find the start of this line (backtrack to previous newline)
        executor_start = content.rfind("\n", 0, executor_text_pos) + 1

        # Find the end of the method (next async def at same indentation level)
        # Look for "\n    async def " which indicates next method
        executor_end = content.find("\n    async def _write_test_file(", executor_start)
        if executor_end == -1:
            raise IntegrationError("Could not find end of _spawn_executor method")

        # Replace the entire _spawn_executor method
        new_executor_method = '''    async def _spawn_executor(self, plan_msg: TrinityMessage) -> None:
        """
        Spawn EXECUTOR agent via HybridExecutor (with local-first + cloud escalation).

        Enhanced workflow:
        1. Extract task from plan message
        2. Determine task type and complexity
        3. Create execution task
        4. Delegate to HybridExecutor (handles escalation automatically)
        5. Publish results to bus
        """
        self.logger.info("⚡ Spawning EXECUTOR via HybridExecutor...")

        # Extract task details from plan
        plan_data = plan_msg.data
        task_type = plan_data.get("task_type", "general")
        complexity = plan_data.get("complexity", "medium")

        # Check if HybridExecutor is initialized
        if not hasattr(self, "hybrid_executor") or self.hybrid_executor is None:
            self.logger.warning(
                "⚠️  HybridExecutor not initialized. Falling back to legacy executor."
            )
            await self._spawn_executor_legacy(plan_msg)
            return

        try:
            # Create task for HybridExecutor
            task = {
                "task_id": f"trinity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "task_type": task_type,
                "complexity": complexity,
                "plan": plan_data,
                "original_signal": plan_msg.data.get("original_signal", {}),
            }

            # Execute via HybridExecutor (handles escalation internally)
            # In production, this would publish to execution_queue and let
            # HybridExecutor's event loop handle it. For now, simulate direct call.
            self.logger.info(
                f"📋 Task created: type={task_type}, complexity={complexity}"
            )

            # Publish to execution queue (HybridExecutor subscribes to this)
            await self._message_bus.publish("execution_queue", task)

            # For synchronous compatibility, wait briefly for result
            # (In production, this would be fully async event-driven)
            self.logger.info("✅ Task published to HybridExecutor queue")

            # Legacy: Also publish EXECUTOR_COMPLETE for Trinity bus compatibility
            self.bus.publish(
                "EXECUTOR",
                "EXECUTOR_COMPLETE",
                {
                    "task_id": task["task_id"],
                    "status": "queued",
                    "executor": "hybrid",
                    "message": "Task queued for HybridExecutor processing",
                },
            )

        except Exception as e:
            self.logger.error(f"❌ HybridExecutor failed: {e}", exc_info=True)
            # Fallback to legacy executor
            self.logger.info("🔄 Falling back to legacy executor...")
            await self._spawn_executor_legacy(plan_msg)

    async def _spawn_executor_legacy(self, plan_msg: TrinityMessage) -> None:
        """
        Legacy EXECUTOR spawning (hardcoded Ollama execution).

        DEPRECATED: Use HybridExecutor for production.
        Kept for backward compatibility and fallback.
        """'''

        # Find the original method and rename it to _spawn_executor_legacy
        # This preserves the original implementation as fallback
        original_method_start = executor_start
        original_method_header_end = content.find(":\n", original_method_start)

        # Replace method header
        legacy_header = '    async def _spawn_executor_legacy(self, plan_msg: TrinityMessage) -> None:\n        """\n        Legacy EXECUTOR spawning (hardcoded Ollama execution).\n\n        DEPRECATED: Use HybridExecutor for production.\n        Kept for backward compatibility and fallback.\n        """'

        # Extract original method body (keep everything after docstring)
        original_body_start = content.find('"""', original_method_header_end + 2)
        if original_body_start == -1:
            original_body_start = original_method_header_end
        else:
            original_body_start = content.find('"""', original_body_start + 3) + 3

        original_body = content[original_body_start:executor_end]

        # Construct new content
        updated_content = (
            content[:executor_start]
            + new_executor_method
            + "\n\n"
            + legacy_header
            + original_body
        )

        if not self.dry_run:
            self.orchestrator_path.write_text(updated_content)
            self.changes_made = True
            logger.info("✅ Executor spawning updated (legacy preserved as fallback)")
        else:
            logger.info(
                "✅ Would update executor spawning (legacy preserved as fallback)"
            )

    def _add_config_loading(self) -> None:
        """Add HybridExecutor initialization to __init__ method."""
        content = self.orchestrator_path.read_text()

        # Check if already has HybridExecutor initialization IN __INIT__ METHOD
        # (not just usage in other methods from previous step)
        init_start = content.find("def __init__(")
        if init_start == -1:
            raise IntegrationError("Could not find __init__ method")

        # Find end of __init__ (next method definition)
        next_method = content.find("\n    def ", init_start + 20)
        if next_method == -1:
            next_method = len(content)

        init_section = content[init_start:next_method]

        if "self.hybrid_executor = create_hybrid_executor(" in init_section:
            logger.warning(
                "⚠️  HybridExecutor already initialized in __init__. Skipping config loading."
            )
            return

        # Find the line with self.ollama initialization
        ollama_init = content.find("self.ollama = OllamaClient(", init_start)
        if ollama_init == -1:
            raise IntegrationError("Could not find self.ollama initialization")

        # Find end of that line
        ollama_line_end = content.find("\n", ollama_init)

        # Insert HybridExecutor initialization after ollama
        hybrid_init = """

        # HybridExecutor initialization (added by integration script)
        # Initialize shared infrastructure for hybrid execution
        try:
            # Create shared context for all agents
            self._agent_context = AgentContext()

            # Create cost tracker
            self._cost_tracker = CostTracker()

            # Create message bus (in-memory for now)
            self._message_bus = MessageBus()

            # Create agent registry with local-first default
            self._agent_registry = create_agent_registry(
                agent_context=self._agent_context,
                cost_tracker=self._cost_tracker,
                default_tier="local",
            )

            # Create escalation policy from config
            escalation_config = self._config.get("escalation", {})
            self._escalation_policy = create_escalation_policy(
                max_local_attempts=escalation_config.get("max_local_attempts", 2),
                max_local_plus_attempts=escalation_config.get(
                    "max_local_plus_attempts", 1
                ),
                test_failure_threshold=escalation_config.get(
                    "test_failure_threshold", 2
                ),
                confidence_threshold=escalation_config.get("confidence_threshold", 0.5),
            )

            # Create HybridExecutor
            self.hybrid_executor = create_hybrid_executor(
                message_bus=self._message_bus,
                cost_tracker=self._cost_tracker,
                agent_context=self._agent_context,
                agent_registry=self._agent_registry,
                escalation_policy=self._escalation_policy,
            )

            self.logger.info(
                "✅ HybridExecutor initialized with local-first execution"
            )

        except Exception as e:
            self.logger.warning(
                f"⚠️  Failed to initialize HybridExecutor: {e}. "
                "Falling back to legacy executor."
            )
            self.hybrid_executor = None
"""

        updated_content = (
            content[: ollama_line_end + 1] + hybrid_init + content[ollama_line_end + 1 :]
        )

        if not self.dry_run:
            self.orchestrator_path.write_text(updated_content)
            self.changes_made = True
            logger.info("✅ HybridExecutor initialization added to __init__")
        else:
            logger.info("✅ Would add HybridExecutor initialization to __init__")

    def _verify_changes(self) -> None:
        """Verify modifications are syntactically correct."""
        if self.dry_run:
            logger.info("✅ Skipping verification (dry run)")
            return

        # Try to compile the modified file
        try:
            content = self.orchestrator_path.read_text()

            # TEMPORARY: Save for debugging
            debug_path = Path("/tmp/orchestrator_debug.py")
            debug_path.write_text(content)
            logger.info(f"DEBUG: Modified file saved to {debug_path}")

            compile(content, str(self.orchestrator_path), "exec")
            logger.info("✅ Modified file is syntactically valid")

        except SyntaxError as e:
            logger.error(f"❌ Syntax error at line {e.lineno}: {e.msg}")
            logger.error(f"DEBUG: Check /tmp/orchestrator_debug.py around line {e.lineno}")
            raise IntegrationError(
                f"Syntax error in modified file: {e}. Rolling back..."
            ) from e

        # Check that all expected components are present
        expected_strings = [
            "from trinity_protocol.core.hybrid_executor import",
            "self.hybrid_executor",
            "async def _spawn_executor_legacy(",
            "HybridExecutor initialized",
        ]

        missing = [s for s in expected_strings if s not in content]
        if missing:
            raise IntegrationError(
                f"Missing expected components: {missing}. Rolling back..."
            )

        logger.info("✅ All expected components present")

    def _rollback(self) -> None:
        """Rollback changes by restoring from backup."""
        if not self.backup_path or not self.backup_path.exists():
            logger.error("❌ Cannot rollback: no backup found")
            return

        try:
            shutil.copy2(self.backup_path, self.orchestrator_path)
            logger.info(f"✅ Rolled back from {self.backup_path}")
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            logger.error(f"⚠️  Manual restoration required from {self.backup_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Integrate HybridExecutor into Trinity Local orchestrator"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying them",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts",
    )
    parser.add_argument(
        "--trinity-home",
        type=str,
        default="~/.trinity-local",
        help="Trinity Local installation directory (default: ~/.trinity-local)",
    )
    parser.add_argument(
        "--agency-root",
        type=str,
        help="Agency OS repository root (default: current directory)",
    )

    args = parser.parse_args()

    # Confirmation prompt (unless --force or --dry-run)
    if not args.force and not args.dry_run:
        print("\n" + "=" * 60)
        print("Trinity Local → HybridExecutor Integration")
        print("=" * 60)
        print("\nThis script will:")
        print("  1. Create a backup of your current orchestrator.py")
        print("  2. Update imports to include HybridExecutor")
        print("  3. Modify executor spawning to use hybrid execution")
        print("  4. Add configuration loading from trinity_hybrid_config.yaml")
        print("  5. Preserve legacy executor as fallback")
        print(f"\nTarget: {Path(args.trinity_home).expanduser()}")
        print("\nA backup will be created before any changes.")
        print("\nProceed? [y/N] ", end="")

        response = input().strip().lower()
        if response not in ["y", "yes"]:
            print("❌ Integration cancelled by user")
            return 1

    # Run integration
    integrator = HybridExecutorIntegrator(
        trinity_home=args.trinity_home,
        agency_root=args.agency_root,
        dry_run=args.dry_run,
    )

    success = integrator.run()

    if success:
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Restart Trinity Local orchestrator:")
        print("   python ~/.trinity-local/trinity_protocol/core/orchestrator.py")
        print("\n2. Monitor logs for HybridExecutor activity:")
        print("   tail -f ~/.trinity-local/logs/trinity.log")
        print("\n3. Verify hybrid execution is working:")
        print("   - Check for 'HybridExecutor initialized' log message")
        print("   - Monitor local vs cloud escalations")
        print("   - Review cost tracking metrics")
        print("\n4. If issues occur:")
        print(f"   - Restore from backup: {integrator.backup_path}")
        print("   - Check logs for error details")
        print("   - Report issues with backup file attached")
        print("=" * 60)
        return 0
    else:
        print("\n❌ Integration failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
