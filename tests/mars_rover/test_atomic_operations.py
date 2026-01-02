"""
Mars Rover Reliability - Phase 1: Atomic Operations Tests.

Constitutional Compliance:
- Article VI: TDD (Tests written FIRST)
- Article I: Complete context (atomic ops ensure consistency)
- Article III: Automated enforcement (rollback on failure)

Acceptance Criteria:
1. Operations are truly atomic (all-or-nothing)
2. Rollback works on partial failure
3. Concurrent operations are handled safely
4. Transaction logging for audit
5. Nested transactions supported
"""

import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestAtomicOperationBasics:
    """Basic atomic operation tests."""

    def test_successful_operation_commits(self) -> None:
        """Successful operations should commit changes."""
        from tools.mars_rover.atomic_operations import AtomicOperation, TransactionManager

        manager = TransactionManager()
        results: list[str] = []

        def operation():
            results.append("executed")
            return "success"

        with manager.transaction() as tx:
            tx.execute(operation)

        assert "executed" in results, "Operation should be executed"
        assert tx.committed, "Transaction should be committed"

    def test_failed_operation_rolls_back(self) -> None:
        """Failed operations should rollback all changes."""
        from tools.mars_rover.atomic_operations import AtomicOperation, TransactionManager

        manager = TransactionManager()
        results: list[str] = []

        def operation1():
            results.append("op1")
            return "success"

        def operation2():
            results.append("op2")
            raise ValueError("Intentional failure")

        def rollback1():
            results.remove("op1")

        def rollback2():
            results.remove("op2")

        try:
            with manager.transaction() as tx:
                tx.execute(operation1, rollback=rollback1)
                tx.execute(operation2, rollback=rollback2)
        except ValueError:
            pass  # Expected

        assert "op1" not in results, "Op1 should be rolled back"
        assert "op2" not in results, "Op2 should be rolled back"
        assert tx.rolled_back, "Transaction should be marked as rolled back"

    def test_all_or_nothing_semantics(self) -> None:
        """Either all operations succeed or none do."""
        from tools.mars_rover.atomic_operations import TransactionManager

        manager = TransactionManager()
        state = {"value": 0}

        def increment():
            state["value"] += 1
            return state["value"]

        def decrement():
            state["value"] -= 1

        def fail_op():
            raise RuntimeError("Simulated failure")

        try:
            with manager.transaction() as tx:
                tx.execute(increment, rollback=decrement)
                tx.execute(increment, rollback=decrement)
                tx.execute(fail_op)
        except RuntimeError:
            pass

        assert state["value"] == 0, "State should be rolled back to initial"


class TestAtomicRollback:
    """Rollback behavior tests."""

    def test_rollback_in_reverse_order(self) -> None:
        """Rollback should happen in reverse order of execution."""
        from tools.mars_rover.atomic_operations import TransactionManager

        manager = TransactionManager()
        rollback_order: list[int] = []

        def op(n):
            return n

        def rollback(n):
            rollback_order.append(n)

        try:
            with manager.transaction() as tx:
                tx.execute(lambda: op(1), rollback=lambda: rollback(1))
                tx.execute(lambda: op(2), rollback=lambda: rollback(2))
                tx.execute(lambda: op(3), rollback=lambda: rollback(3))
                raise Exception("Trigger rollback")
        except Exception:
            pass

        assert rollback_order == [3, 2, 1], (
            f"Rollback should be in reverse order, got {rollback_order}"
        )

    def test_partial_rollback_on_rollback_failure(self) -> None:
        """If rollback fails, log error and continue with remaining rollbacks."""
        from tools.mars_rover.atomic_operations import TransactionManager

        manager = TransactionManager()
        rollback_results: list[str] = []

        def op(n):
            return n

        def good_rollback(n):
            rollback_results.append(f"rolled_back_{n}")

        def bad_rollback():
            raise RuntimeError("Rollback failed")

        try:
            with manager.transaction() as tx:
                tx.execute(lambda: op(1), rollback=lambda: good_rollback(1))
                tx.execute(lambda: op(2), rollback=bad_rollback)
                tx.execute(lambda: op(3), rollback=lambda: good_rollback(3))
                raise Exception("Trigger rollback")
        except Exception:
            pass

        # Good rollbacks should still execute
        assert "rolled_back_3" in rollback_results
        assert "rolled_back_1" in rollback_results


class TestConcurrentOperations:
    """Concurrent operation safety tests."""

    def test_concurrent_transactions_isolated(self) -> None:
        """Concurrent transactions should not interfere with each other."""
        from tools.mars_rover.atomic_operations import TransactionManager

        manager = TransactionManager()
        results: dict[str, list[str]] = {"tx1": [], "tx2": []}

        def tx1_work():
            time.sleep(0.01)
            results["tx1"].append("work")
            return "tx1_done"

        def tx2_work():
            results["tx2"].append("work")
            return "tx2_done"

        def run_tx1():
            with manager.transaction() as tx:
                tx.execute(tx1_work)

        def run_tx2():
            with manager.transaction() as tx:
                tx.execute(tx2_work)

        t1 = threading.Thread(target=run_tx1)
        t2 = threading.Thread(target=run_tx2)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert "work" in results["tx1"], "TX1 should complete"
        assert "work" in results["tx2"], "TX2 should complete"

    def test_lock_prevents_race_conditions(self) -> None:
        """Shared resource access should be protected by locks."""
        from tools.mars_rover.atomic_operations import TransactionManager

        manager = TransactionManager()
        shared_counter = {"value": 0}
        iterations = 100

        def increment():
            current = shared_counter["value"]
            time.sleep(0.0001)  # Simulate some work
            shared_counter["value"] = current + 1

        def decrement():
            shared_counter["value"] -= 1

        def run_increments():
            for _ in range(iterations):
                with manager.transaction() as tx:
                    tx.execute(increment, rollback=decrement)

        threads = [threading.Thread(target=run_increments) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # With proper locking, final value should be 500
        # Without locking, it would be less due to race conditions
        assert shared_counter["value"] == 500, (
            f"Expected 500, got {shared_counter['value']} (race condition detected)"
        )


class TestTransactionLogging:
    """Transaction audit logging tests."""

    def test_transactions_are_logged(self) -> None:
        """All transactions should be logged for audit."""
        from tools.mars_rover.atomic_operations import TransactionManager

        manager = TransactionManager()

        with manager.transaction() as tx:
            tx.execute(lambda: "result")

        logs = manager.get_transaction_log()

        assert len(logs) >= 1, "Transaction should be logged"
        assert logs[-1]["status"] == "committed"

    def test_failed_transactions_logged(self) -> None:
        """Failed transactions should be logged with error details."""
        from tools.mars_rover.atomic_operations import TransactionManager

        manager = TransactionManager()

        try:
            with manager.transaction() as tx:
                tx.execute(lambda: None)
                raise ValueError("Test error")
        except ValueError:
            pass

        logs = manager.get_transaction_log()

        assert any(log["status"] == "rolled_back" for log in logs), (
            "Rollback should be logged"
        )


class TestNestedTransactions:
    """Nested transaction tests."""

    def test_nested_transactions_supported(self) -> None:
        """Nested transactions should be supported via savepoints."""
        from tools.mars_rover.atomic_operations import TransactionManager

        manager = TransactionManager()
        results: list[str] = []

        with manager.transaction() as outer:
            outer.execute(lambda: results.append("outer"))

            with manager.transaction() as inner:
                inner.execute(lambda: results.append("inner"))

        assert "outer" in results
        assert "inner" in results

    def test_inner_rollback_preserves_outer(self) -> None:
        """Inner transaction rollback should not affect outer transaction."""
        from tools.mars_rover.atomic_operations import TransactionManager

        manager = TransactionManager()
        results: list[str] = []

        def add_outer():
            results.append("outer")

        def add_inner():
            results.append("inner")

        def remove_inner():
            if "inner" in results:
                results.remove("inner")

        with manager.transaction() as outer:
            outer.execute(add_outer)

            try:
                with manager.transaction() as inner:
                    inner.execute(add_inner, rollback=remove_inner)
                    raise ValueError("Inner fails")
            except ValueError:
                pass  # Inner rolled back

        # Outer should still be there, inner should be rolled back
        assert "outer" in results, "Outer should be preserved"
        assert "inner" not in results, "Inner should be rolled back"


class TestFileOperations:
    """Atomic file operation tests."""

    def test_atomic_file_write(self) -> None:
        """File writes should be atomic (write to temp, then rename)."""
        from tools.mars_rover.atomic_operations import AtomicFileWriter

        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir) / "test_file.txt"
            content = "Test content"

            writer = AtomicFileWriter(target_path)
            writer.write(content)

            assert target_path.exists(), "File should exist after write"
            assert target_path.read_text() == content, "Content should match"

    def test_atomic_file_write_rollback(self) -> None:
        """Failed atomic file write should not leave partial file."""
        from tools.mars_rover.atomic_operations import AtomicFileWriter

        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir) / "test_file.txt"
            original_content = "Original"

            # Write original
            target_path.write_text(original_content)

            # Attempt atomic write that fails
            writer = AtomicFileWriter(target_path)

            try:
                with writer.atomic_write() as f:
                    f.write("New content")
                    raise ValueError("Simulated failure")
            except ValueError:
                pass

            # Original should be preserved
            assert target_path.read_text() == original_content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
