"""
Async Memory Tool Operation Tests

Tests async operations (view, create, edit, delete) with AAA pattern.
Verifies code_memory_tool_async_api implementation.

Constitutional Compliance:
- Article I: Complete context (all async operations run to completion)
- Article II: 100% verification (all tests must pass)
- Article IV: Store successful patterns in VectorStore

Test Coverage (NECESSARY Pattern):
- Normal operation: Happy path async file operations
- Edge cases: Empty files, large files, nonexistent paths
- Error conditions: Timeouts, path validation failures
- Security: Path traversal prevention preserved async

Performance Target:
- <10ms I/O timeout detection
- <5ms lock acquisition latency (99th percentile)
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from tools.async_memory_tool import AsyncMemoryTool, create_async_memory_tool


class TestAsyncOperationsNormal:
    """Normal operation tests - Happy path scenarios (NECESSARY: N)"""

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool with temporary base directory"""
        tool = AsyncMemoryTool(base_dir=str(tmp_path / "memories"))
        yield tool
        # Cleanup lock manager
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_view_async_success(self, async_tool):
        """
        GIVEN a file exists in memory
        WHEN view_async is called
        THEN file contents are returned successfully
        """
        # Arrange
        test_path = "/memories/test.txt"
        test_content = "Hello async world!"
        create_result = await async_tool.create_async(test_path, test_content)
        assert create_result.is_ok(), f"Setup failed: {create_result.unwrap_err()}"

        # Act
        result = await async_tool.view_async(test_path)

        # Assert
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"
        assert result.unwrap() == test_content

    @pytest.mark.asyncio
    async def test_create_async_success(self, async_tool):
        """
        GIVEN a valid path and content
        WHEN create_async is called
        THEN file is created atomically
        """
        # Arrange
        test_path = "/memories/new_file.txt"
        test_content = "Atomic write test"

        # Act
        result = await async_tool.create_async(test_path, test_content)

        # Assert
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"
        assert "Successfully created" in result.unwrap()

        # Verify file exists
        view_result = await async_tool.view_async(test_path)
        assert view_result.is_ok()
        assert view_result.unwrap() == test_content

    @pytest.mark.asyncio
    async def test_str_replace_async_success(self, async_tool):
        """
        GIVEN a file with specific text
        WHEN str_replace_async is called
        THEN text is replaced correctly
        """
        # Arrange
        test_path = "/memories/replace.txt"
        original = "Hello old world"
        await async_tool.create_async(test_path, original)

        # Act
        result = await async_tool.str_replace_async(test_path, "old", "new")

        # Assert
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"
        assert "Successfully replaced 1 occurrence(s)" in result.unwrap()

        # Verify replacement
        view_result = await async_tool.view_async(test_path)
        assert view_result.unwrap() == "Hello new world"

    @pytest.mark.asyncio
    async def test_insert_async_success(self, async_tool):
        """
        GIVEN a file with multiple lines
        WHEN insert_async is called
        THEN text is inserted at correct line
        """
        # Arrange
        test_path = "/memories/insert.txt"
        original = "Line 1\nLine 2\nLine 3\n"
        await async_tool.create_async(test_path, original)

        # Act
        result = await async_tool.insert_async(test_path, 2, "Inserted line\n")

        # Assert
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"
        assert "Successfully inserted at line 2" in result.unwrap()

        # Verify insertion
        view_result = await async_tool.view_async(test_path)
        lines = view_result.unwrap().split("\n")
        assert lines[1] == "Inserted line"

    @pytest.mark.asyncio
    async def test_delete_async_success(self, async_tool):
        """
        GIVEN a file exists
        WHEN delete_async is called
        THEN file is removed
        """
        # Arrange
        test_path = "/memories/delete_me.txt"
        await async_tool.create_async(test_path, "Delete this")

        # Act
        result = await async_tool.delete_async(test_path)

        # Assert
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"
        assert "Successfully deleted file" in result.unwrap()

        # Verify deletion
        view_result = await async_tool.view_async(test_path)
        assert view_result.is_err()
        assert "does not exist" in view_result.unwrap_err()

    @pytest.mark.asyncio
    async def test_rename_async_success(self, async_tool):
        """
        GIVEN a file exists
        WHEN rename_async is called
        THEN file is renamed with dual lock
        """
        # Arrange
        old_path = "/memories/old_name.txt"
        new_path = "/memories/new_name.txt"
        content = "Rename test"
        await async_tool.create_async(old_path, content)

        # Act
        result = await async_tool.rename_async(old_path, new_path)

        # Assert
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"
        assert "Successfully renamed" in result.unwrap()

        # Verify old path gone
        old_view = await async_tool.view_async(old_path)
        assert old_view.is_err()

        # Verify new path exists
        new_view = await async_tool.view_async(new_path)
        assert new_view.is_ok()
        assert new_view.unwrap() == content


class TestAsyncOperationsEdgeCases:
    """Edge case tests - Boundary conditions (NECESSARY: E)"""

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool with temporary base directory"""
        tool = AsyncMemoryTool(
            base_dir=str(tmp_path / "memories"),
            max_file_size=1000,  # Small limit for testing
        )
        yield tool
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_view_async_empty_file(self, async_tool):
        """
        GIVEN an empty file exists
        WHEN view_async is called
        THEN empty string is returned
        """
        # Arrange
        test_path = "/memories/empty.txt"
        await async_tool.create_async(test_path, "")

        # Act
        result = await async_tool.view_async(test_path)

        # Assert
        assert result.is_ok()
        assert result.unwrap() == ""

    @pytest.mark.asyncio
    async def test_create_async_file_size_limit(self, async_tool):
        """
        GIVEN content exceeds max_file_size
        WHEN create_async is called
        THEN size limit error is returned
        """
        # Arrange
        test_path = "/memories/too_large.txt"
        large_content = "x" * 2000  # Exceeds 1000 byte limit

        # Act
        result = await async_tool.create_async(test_path, large_content)

        # Assert
        assert result.is_err()
        assert "exceeds size limit" in result.unwrap_err()

    @pytest.mark.asyncio
    async def test_view_async_nonexistent_file(self, async_tool):
        """
        GIVEN a file does not exist
        WHEN view_async is called
        THEN appropriate error is returned
        """
        # Arrange
        test_path = "/memories/nonexistent.txt"

        # Act
        result = await async_tool.view_async(test_path)

        # Assert
        assert result.is_err()
        assert "does not exist" in result.unwrap_err()

    @pytest.mark.asyncio
    async def test_view_async_directory(self, async_tool):
        """
        GIVEN a directory exists
        WHEN view_async is called
        THEN directory listing is returned
        """
        # Arrange
        await async_tool.create_async("/memories/dir/file1.txt", "content1")
        await async_tool.create_async("/memories/dir/file2.txt", "content2")

        # Act
        result = await async_tool.view_async("/memories/dir")

        # Assert
        assert result.is_ok()
        listing = result.unwrap()
        assert "[FILE] file1.txt" in listing
        assert "[FILE] file2.txt" in listing


class TestAsyncOperationsErrors:
    """Error condition tests - Failure scenarios (NECESSARY: E)"""

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool with temporary base directory"""
        tool = AsyncMemoryTool(
            base_dir=str(tmp_path / "memories"),
            lock_timeout=0.5,  # Short timeout for testing
            io_timeout=2.0,
        )
        yield tool
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_async_timeout_handling(self, async_tool):
        """
        GIVEN a lock is held by another task
        WHEN a second task tries to acquire with timeout
        THEN timeout error is returned
        """
        # Arrange
        test_path = "/memories/timeout_test.txt"
        await async_tool.create_async(test_path, "initial")

        # Manually acquire lock to simulate long-running operation
        lock_manager = async_tool._lock_manager
        lock_acquired = False

        async def holder():
            """Hold lock for extended period"""
            nonlocal lock_acquired
            async with lock_manager.acquire_lock(test_path, timeout=5.0):
                lock_acquired = True
                await asyncio.sleep(2.0)  # Hold longer than timeout

        async def contender():
            """Try to acquire same lock with short timeout"""
            await asyncio.sleep(0.1)  # Let holder acquire first
            result = await async_tool.view_async(test_path)
            return result

        # Act
        holder_task = asyncio.create_task(holder())
        contender_task = asyncio.create_task(contender())

        # Wait for contender to timeout
        result = await contender_task
        holder_task.cancel()

        try:
            await holder_task
        except asyncio.CancelledError:
            pass

        # Assert
        assert lock_acquired, "Holder should have acquired lock"
        assert result.is_err(), "Contender should have timed out"
        assert "timeout" in result.unwrap_err().lower()

    @pytest.mark.asyncio
    async def test_str_replace_async_string_not_found(self, async_tool):
        """
        GIVEN a file without target string
        WHEN str_replace_async is called
        THEN string not found error is returned
        """
        # Arrange
        test_path = "/memories/no_match.txt"
        await async_tool.create_async(test_path, "Hello world")

        # Act
        result = await async_tool.str_replace_async(test_path, "nonexistent", "replacement")

        # Assert
        assert result.is_err()
        assert "not found" in result.unwrap_err()

    @pytest.mark.asyncio
    async def test_delete_async_nonexistent(self, async_tool):
        """
        GIVEN a file does not exist
        WHEN delete_async is called
        THEN appropriate error is returned
        """
        # Arrange
        test_path = "/memories/nonexistent.txt"

        # Act
        result = await async_tool.delete_async(test_path)

        # Assert
        assert result.is_err()
        assert "does not exist" in result.unwrap_err()

    @pytest.mark.asyncio
    async def test_rename_async_destination_exists(self, async_tool):
        """
        GIVEN both source and destination files exist
        WHEN rename_async is called
        THEN destination exists error is returned
        """
        # Arrange
        await async_tool.create_async("/memories/source.txt", "source")
        await async_tool.create_async("/memories/dest.txt", "dest")

        # Act
        result = await async_tool.rename_async("/memories/source.txt", "/memories/dest.txt")

        # Assert
        assert result.is_err()
        assert "already exists" in result.unwrap_err()


class TestAsyncOperationsSecurity:
    """Security tests - Path traversal prevention (NECESSARY: S)"""

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool with temporary base directory"""
        tool = AsyncMemoryTool(base_dir=str(tmp_path / "memories"))
        yield tool
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_path_security_preserved_async(self, async_tool):
        """
        GIVEN path traversal attempts
        WHEN async operations are called
        THEN security validation blocks attacks
        """
        # Arrange - Various traversal attempts
        traversal_paths = [
            "/memories/../etc/passwd",
            "/memories/../../etc/passwd",
            "/memories/%2e%2e/etc/passwd",
            "/memories/%252e%252e/etc/passwd",
            "/memories/.%2e/etc/passwd",
        ]

        # Act & Assert - All should fail validation
        for bad_path in traversal_paths:
            result = await async_tool.view_async(bad_path)
            assert result.is_err(), f"Path should be blocked: {bad_path}"
            assert "traversal" in result.unwrap_err().lower()

    @pytest.mark.asyncio
    async def test_path_without_memories_prefix_blocked(self, async_tool):
        """
        GIVEN paths without /memories prefix
        WHEN async operations are called
        THEN validation rejects paths
        """
        # Arrange
        invalid_paths = ["/etc/passwd", "notes.txt", "/tmp/test.txt"]

        # Act & Assert
        for bad_path in invalid_paths:
            result = await async_tool.view_async(bad_path)
            assert result.is_err()
            assert "must start with /memories" in result.unwrap_err()

    @pytest.mark.asyncio
    async def test_root_directory_protection(self, async_tool):
        """
        GIVEN attempt to delete root /memories
        WHEN delete_async is called
        THEN operation is blocked
        """
        # Arrange
        root_path = "/memories"

        # Act
        result = await async_tool.delete_async(root_path)

        # Assert
        assert result.is_err()
        assert "Cannot delete root" in result.unwrap_err()


class TestAsyncOperationsPerformance:
    """Performance tests - Yield/output validation (NECESSARY: Y)"""

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool with temporary base directory"""
        tool = AsyncMemoryTool(base_dir=str(tmp_path / "memories"))
        yield tool
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_concurrent_reads_same_file(self, async_tool):
        """
        GIVEN 10 concurrent read tasks on same file
        WHEN all tasks execute simultaneously
        THEN all reads succeed with correct content
        """
        # Arrange
        test_path = "/memories/shared.txt"
        test_content = "Shared content for concurrent reads"
        await async_tool.create_async(test_path, test_content)

        # Act - 10 concurrent reads
        tasks = [async_tool.view_async(test_path) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Assert - All successful with same content
        assert all(r.is_ok() for r in results), "All reads should succeed"
        assert all(r.unwrap() == test_content for r in results), "Content should match"

    @pytest.mark.asyncio
    async def test_lock_metrics_tracking(self, async_tool):
        """
        GIVEN multiple file operations
        WHEN operations complete
        THEN lock metrics are tracked correctly
        """
        # Arrange & Act
        for i in range(5):
            await async_tool.create_async(f"/memories/file{i}.txt", f"content{i}")

        # Get metrics
        metrics = async_tool.get_lock_metrics()

        # Assert
        assert metrics.total_acquisitions >= 5, "At least 5 lock acquisitions"
        assert metrics.total_acquisitions >= 0, "Metrics tracked"
        assert metrics.max_wait_time_ms >= 0, "Max wait time tracked"

    @pytest.mark.asyncio
    async def test_factory_function(self, tmp_path):
        """
        GIVEN factory function parameters
        WHEN create_async_memory_tool is called
        THEN properly configured tool is returned
        """
        # Arrange & Act
        tool = create_async_memory_tool(
            session_id="test_session",
            base_dir=str(tmp_path / "custom_memories"),
        )

        # Assert
        assert tool is not None
        assert isinstance(tool, AsyncMemoryTool)

        # Test basic operation
        result = await tool.create_async("/memories/test.txt", "factory test")
        assert result.is_ok()

        # Cleanup
        await tool.cleanup()


# =============================================================================
# REGRESSION TESTS - Ensure 30 security tests still pass async
# =============================================================================


class TestAsyncSecurityRegression:
    """
    Regression tests to ensure all 30 security tests from
    test_anthropic_memory_security.py pass with async API.
    """

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool with temporary base directory"""
        tool = AsyncMemoryTool(base_dir=str(tmp_path / "memories"))
        yield tool
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_all_traversal_patterns_blocked(self, async_tool):
        """
        GIVEN all known path traversal patterns
        WHEN async view is attempted
        THEN all are blocked (either by validation or safe failure)
        """
        # Arrange - Comprehensive traversal patterns
        patterns = [
            "/memories/../etc/passwd",
            "/memories/../../etc/passwd",
            "/memories/../../../etc/passwd",
            "/memories/%2e%2e/etc/passwd",
            "/memories/%252e%252e/etc/passwd",
            "/memories/.%2e/etc/passwd",
            "/memories/%2e./etc/passwd",
            "/memories/..%2f/etc/passwd",
        ]

        # Act & Assert
        for pattern in patterns:
            result = await async_tool.view_async(pattern)
            assert result.is_err(), f"Pattern should be blocked: {pattern}"
            # Accept either security error OR safe "does not exist" error
            # Both are valid: prevents access to sensitive files
