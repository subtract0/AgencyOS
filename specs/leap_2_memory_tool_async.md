# Leap 2: Memory Tool Async/Await Refactoring Spec

**Created:** 2025-10-10
**Status:** Phase 1, Task 3 (Parallel Execution)
**Type:** Spec (Design)
**Tier:** Tier 1 (Foundation)
**Task Graph Reference:** Leap 2, Phase 1, Task 3 of 4

---

## Executive Summary

This spec defines **async/await patterns** for Memory Tool operations to enable **parallel memory reads/writes** across agents while maintaining **security** and **constitutional compliance**. The refactoring will eliminate I/O blocking bottlenecks and enable 3x throughput improvement through batch operations.

**Key Objectives:**
- Convert synchronous file I/O to async/await pattern
- Implement per-file concurrency control (asyncio.Lock)
- Design batch_view() API for parallel reads (3x speedup)
- Maintain backward compatibility with sync callers
- Preserve all security validations (path traversal prevention)

**Success Criteria:**
- All 6 memory operations converted to async
- Deadlock-free concurrency control with timeout detection
- 3x throughput improvement on parallel reads (benchmark)
- 30 security tests pass with zero regressions
- Sync wrapper maintains API compatibility

---

## 1. Constitutional Compliance

### Article I: Complete Context Before Action
- **Async timeout handling:** All async operations use `asyncio.wait_for()` with 2x, 3x, 10x retry progression
- **No partial writes:** Atomic file operations with rollback on incomplete data
- **Retry pattern:** `ensure_complete_context_async()` wrapper for all I/O

### Article II: 100% Verification and Stability
- **30 security tests:** All existing tests must pass after async conversion
- **Atomicity:** File operations are transactional (create → write → rename)
- **No broken windows:** Async exceptions properly propagated, never swallowed

### Article III: Automated Merge Enforcement
- **Type safety:** `async def` signatures with strict return types (`-> Result[str, str]`)
- **Linting:** `ruff` async rules enabled (no-blocking-io, async-function-call)
- **CI validation:** Async tests run in GitHub Actions with timeout enforcement

### Article IV: Continuous Learning and Improvement
- **Pattern storage:** Store async deadlock detections in VectorStore
- **Telemetry:** Track lock contention metrics for optimization
- **Query learnings:** Use `/agent-memory-query architecture async` before implementation

### Article V: Spec-Driven Development
- **This spec drives implementation:** All code traces back to this document
- **Plan.md reference:** Implementation plan in `plans/leap_2_memory_async_plan.md`
- **TodoWrite tasks:** Break down into 8 sequential tasks with verification gates

---

## 2. Async API Design

### 2.1 Async Function Signatures

```python
from typing import Optional
from shared.type_definitions.result import Result
import asyncio
import aiofiles

class AsyncMemoryTool(BetaAbstractMemoryTool):
    """Async version of Memory Tool with concurrency control.

    All operations use aiofiles for non-blocking I/O.
    Per-file locks prevent race conditions during concurrent access.
    """

    def __init__(
        self,
        base_dir: str | None = None,
        max_file_size: int = 1_000_000,
        max_view_lines: int = 1000,
        lock_timeout: float = 5.0,  # NEW: Lock acquisition timeout
        io_timeout: float = 10.0,   # NEW: File I/O timeout
    ):
        # ... existing initialization ...

        # NEW: Per-file lock registry
        self._file_locks: dict[str, asyncio.Lock] = {}
        self._lock_registry_lock = asyncio.Lock()  # Protects _file_locks dict
        self.lock_timeout = lock_timeout
        self.io_timeout = io_timeout

    async def _get_file_lock(self, path: Path) -> asyncio.Lock:
        """Get or create lock for specific file path.

        Thread-safe lock registry access with double-checked locking pattern.
        """
        path_str = str(path)

        # Fast path: lock exists
        if path_str in self._file_locks:
            return self._file_locks[path_str]

        # Slow path: create lock with registry protection
        async with self._lock_registry_lock:
            # Double-check after acquiring registry lock
            if path_str not in self._file_locks:
                self._file_locks[path_str] = asyncio.Lock()
            return self._file_locks[path_str]

    # ========================================================================
    # ASYNC API (6 operations)
    # ========================================================================

    async def view_async(
        self,
        path: str,
        view_range: list[int] | None = None
    ) -> Result[str, str]:
        """Async view directory or file contents.

        Uses shared lock (multiple concurrent readers allowed).
        Timeout: self.io_timeout (default 10s).

        Returns:
            Ok(content) on success, Err(error_msg) on failure.
        """
        try:
            full_path = self._validate_path(path)  # Sync validation

            if not full_path.exists():
                return Err(f"Path does not exist: {path}")

            # Directory listing (no lock needed, read-only metadata)
            if full_path.is_dir():
                return Ok(await self._list_directory_async(full_path))

            # File read with shared lock
            file_lock = await self._get_file_lock(full_path)

            try:
                async with asyncio.timeout(self.lock_timeout):
                    await file_lock.acquire()
            except asyncio.TimeoutError:
                return Err(f"Lock timeout: file busy: {path}")

            try:
                content = await self._read_file_async(full_path, view_range)
                return Ok(content)
            finally:
                file_lock.release()

        except ValueError as e:
            return Err(str(e))
        except asyncio.TimeoutError:
            return Err(f"I/O timeout reading: {path}")
        except Exception as e:
            return Err(f"Unexpected error: {e}")

    async def create_async(
        self,
        path: str,
        file_text: str
    ) -> Result[str, str]:
        """Async create or overwrite file.

        Uses exclusive lock (blocks all other operations).
        Atomic write with temp file + rename for safety.
        """
        try:
            full_path = self._validate_path(path)

            # Size check (before lock acquisition)
            if len(file_text.encode("utf-8")) > self.max_file_size:
                return Err(f"File exceeds size limit ({self.max_file_size} bytes)")

            if full_path.exists() and full_path.is_dir():
                return Err(f"Cannot overwrite directory: {path}")

            # Acquire exclusive lock
            file_lock = await self._get_file_lock(full_path)

            try:
                async with asyncio.timeout(self.lock_timeout):
                    await file_lock.acquire()
            except asyncio.TimeoutError:
                return Err(f"Lock timeout: file busy: {path}")

            try:
                # Atomic write: temp file → rename
                await self._atomic_write_async(full_path, file_text)
                return Ok(f"Successfully created: {path} ({len(file_text)} chars)")
            finally:
                file_lock.release()

        except ValueError as e:
            return Err(str(e))
        except asyncio.TimeoutError:
            return Err(f"I/O timeout writing: {path}")
        except Exception as e:
            return Err(f"Error creating file: {e}")

    async def str_replace_async(
        self,
        path: str,
        old_str: str,
        new_str: str
    ) -> Result[str, str]:
        """Async replace text in file.

        Read-modify-write with exclusive lock.
        """
        try:
            full_path = self._validate_path(path)

            if not full_path.exists():
                return Err(f"File does not exist: {path}")
            if full_path.is_dir():
                return Err(f"Cannot edit directory: {path}")

            file_lock = await self._get_file_lock(full_path)

            try:
                async with asyncio.timeout(self.lock_timeout):
                    await file_lock.acquire()
            except asyncio.TimeoutError:
                return Err(f"Lock timeout: file busy: {path}")

            try:
                # Read
                async with aiofiles.open(full_path, encoding="utf-8") as f:
                    content = await asyncio.wait_for(f.read(), timeout=self.io_timeout)

                # Check existence
                if old_str not in content:
                    return Err(f"String not found: {old_str[:50]}...")

                # Replace
                new_content = content.replace(old_str, new_str)

                # Size check
                if len(new_content.encode("utf-8")) > self.max_file_size:
                    return Err(f"Replacement exceeds size limit ({self.max_file_size} bytes)")

                # Write
                await self._atomic_write_async(full_path, new_content)

                occurrences = content.count(old_str)
                return Ok(f"Successfully replaced {occurrences} occurrence(s) in {path}")
            finally:
                file_lock.release()

        except UnicodeDecodeError:
            return Err(f"File is not valid UTF-8: {path}")
        except asyncio.TimeoutError:
            return Err(f"I/O timeout: {path}")
        except Exception as e:
            return Err(f"Error replacing text: {e}")

    async def insert_async(
        self,
        path: str,
        insert_line: int,
        insert_text: str
    ) -> Result[str, str]:
        """Async insert text at line."""
        # Similar pattern to str_replace_async
        # (Implementation details omitted for brevity)
        pass

    async def delete_async(
        self,
        path: str
    ) -> Result[str, str]:
        """Async delete file/directory."""
        # Exclusive lock, then async os.remove() or shutil.rmtree()
        pass

    async def rename_async(
        self,
        old_path: str,
        new_path: str
    ) -> Result[str, str]:
        """Async rename/move file."""
        # Two locks: old_path and new_path, acquired in sorted order (deadlock prevention)
        pass

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _atomic_write_async(self, path: Path, content: str) -> None:
        """Atomic file write using temp file + rename.

        Pattern:
        1. Write to {path}.tmp
        2. Rename {path}.tmp → {path} (atomic on POSIX)
        3. Delete temp file on error
        """
        temp_path = path.with_suffix(path.suffix + ".tmp")

        try:
            # Create parent dirs
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp
            async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
                await asyncio.wait_for(f.write(content), timeout=self.io_timeout)

            # Atomic rename
            temp_path.rename(path)
        except Exception:
            # Cleanup on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    async def _read_file_async(
        self,
        path: Path,
        view_range: list[int] | None = None
    ) -> str:
        """Read file with optional line range and truncation."""
        async with aiofiles.open(path, encoding="utf-8") as f:
            lines = await asyncio.wait_for(f.readlines(), timeout=self.io_timeout)

        # Apply line range
        if view_range:
            start, end = view_range
            start = max(0, start - 1)
            end = min(len(lines), end)
            lines = lines[start:end]

        # Truncate
        if len(lines) > self.max_view_lines:
            lines = lines[:self.max_view_lines]
            lines.append(f"\n... (truncated, showing first {self.max_view_lines} lines)")

        return "".join(lines)

    async def _list_directory_async(self, path: Path) -> str:
        """Async directory listing."""
        # Use asyncio.to_thread for blocking os.listdir
        entries = await asyncio.to_thread(
            lambda: sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        )

        lines = []
        for entry in entries:
            prefix = "[DIR]" if entry.is_dir() else "[FILE]"
            size = "" if entry.is_dir() else f" ({entry.stat().st_size} bytes)"
            lines.append(f"{prefix} {entry.name}{size}")

        return "\n".join(lines) if lines else "(empty directory)"
```

### 2.2 Batch Operations API

```python
class AsyncMemoryTool:
    """Extended with batch operations for parallel reads."""

    async def batch_view_async(
        self,
        paths: list[str],
        max_concurrency: int = 10
    ) -> dict[str, Result[str, str]]:
        """Parallel view of multiple files.

        Uses asyncio.gather() with semaphore for concurrency control.
        3x faster than sequential view_async() calls.

        Args:
            paths: List of paths to read
            max_concurrency: Max parallel reads (default 10)

        Returns:
            Dict mapping path → Result(content | error)
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _bounded_view(path: str) -> tuple[str, Result[str, str]]:
            async with semaphore:
                result = await self.view_async(path)
                return (path, result)

        # Parallel execution
        tasks = [_bounded_view(path) for path in paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert to dict
        output = {}
        for item in results:
            if isinstance(item, Exception):
                # Should not happen (view_async returns Result), but handle anyway
                output["<error>"] = Err(f"Unexpected exception: {item}")
            else:
                path, result = item
                output[path] = result

        return output

    async def batch_create_async(
        self,
        files: dict[str, str],
        max_concurrency: int = 5  # Lower for write operations
    ) -> dict[str, Result[str, str]]:
        """Parallel create of multiple files.

        Lower concurrency (5 vs 10) to reduce I/O contention on writes.
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _bounded_create(path: str, content: str) -> tuple[str, Result[str, str]]:
            async with semaphore:
                result = await self.create_async(path, content)
                return (path, result)

        tasks = [_bounded_create(path, content) for path, content in files.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for item in results:
            if isinstance(item, Exception):
                output["<error>"] = Err(str(item))
            else:
                path, result = item
                output[path] = result

        return output
```

---

## 3. Concurrency Control Strategy

### 3.1 Lock Hierarchy (Deadlock Prevention)

**Problem:** Multiple agents accessing overlapping files → potential deadlock.

**Solution:** Global lock ordering based on path string comparison.

```python
async def _acquire_multiple_locks(
    self,
    paths: list[Path]
) -> list[asyncio.Lock]:
    """Acquire multiple locks in sorted order to prevent deadlock.

    Example: rename("/memories/a", "/memories/b")
    - Always lock "a" before "b" (alphabetical order)
    - Prevents AB-BA deadlock
    """
    sorted_paths = sorted(paths, key=str)
    locks = []

    for path in sorted_paths:
        lock = await self._get_file_lock(path)
        try:
            async with asyncio.timeout(self.lock_timeout):
                await lock.acquire()
            locks.append(lock)
        except asyncio.TimeoutError:
            # Release already acquired locks
            for acquired_lock in locks:
                acquired_lock.release()
            raise

    return locks
```

### 3.2 Lock Types and Semantics

| Operation | Lock Type | Reasoning |
|-----------|-----------|-----------|
| **view** | Shared (via asyncio.Lock with reader count) | Multiple agents can read simultaneously |
| **create** | Exclusive (asyncio.Lock) | Prevents race during file creation |
| **str_replace** | Exclusive | Read-modify-write requires atomicity |
| **insert** | Exclusive | Modify operation |
| **delete** | Exclusive | Prevents read during deletion |
| **rename** | Exclusive (2 locks) | Both old_path and new_path locked |

**Note:** Python's `asyncio.Lock` does not support shared locks. For true read-write locks, use `asyncio.Condition` or third-party `aiorwlock`.

**Alternative (Future Enhancement):**
```python
from aiorwlock import RWLock

class AsyncMemoryTool:
    def __init__(self):
        self._file_locks: dict[str, RWLock] = {}  # Supports shared reads

    async def view_async(self, path: str) -> Result[str, str]:
        lock = await self._get_file_lock(path)
        async with lock.reader_lock:  # Shared read
            content = await self._read_file_async(path)
            return Ok(content)

    async def create_async(self, path: str, text: str) -> Result[str, str]:
        lock = await self._get_file_lock(path)
        async with lock.writer_lock:  # Exclusive write
            await self._atomic_write_async(path, text)
            return Ok("Success")
```

### 3.3 Timeout and Deadlock Detection

```python
class DeadlockDetector:
    """Monitors lock acquisitions for potential deadlocks."""

    def __init__(self):
        self.lock_graph: dict[asyncio.Task, set[str]] = {}  # Task → held locks
        self.wait_graph: dict[asyncio.Task, str] = {}       # Task → waiting for lock

    async def acquire_with_detection(
        self,
        lock: asyncio.Lock,
        path: str,
        timeout: float = 5.0
    ) -> None:
        """Acquire lock with deadlock detection.

        Raises asyncio.TimeoutError if deadlock suspected.
        Logs deadlock cycle to VectorStore for learning.
        """
        current_task = asyncio.current_task()

        # Record wait
        self.wait_graph[current_task] = path

        try:
            async with asyncio.timeout(timeout):
                await lock.acquire()
        except asyncio.TimeoutError:
            # Detect cycle in wait graph
            cycle = self._detect_cycle(current_task)
            if cycle:
                # Log to VectorStore for learning
                await self._log_deadlock(cycle)
            raise
        finally:
            # Record acquisition
            if current_task in self.wait_graph:
                del self.wait_graph[current_task]
            self.lock_graph.setdefault(current_task, set()).add(path)

    def _detect_cycle(self, start_task: asyncio.Task) -> list[str] | None:
        """Detect cycle in wait-for graph using DFS."""
        visited = set()
        stack = []

        def dfs(task):
            if task in stack:
                # Cycle detected
                cycle_start = stack.index(task)
                return stack[cycle_start:]

            if task in visited:
                return None

            visited.add(task)
            stack.append(task)

            # Follow wait edge
            if task in self.wait_graph:
                waiting_for_path = self.wait_graph[task]
                # Find who holds this lock
                for holder, held_locks in self.lock_graph.items():
                    if waiting_for_path in held_locks:
                        result = dfs(holder)
                        if result:
                            return result

            stack.pop()
            return None

        return dfs(start_task)

    async def _log_deadlock(self, cycle: list[asyncio.Task]) -> None:
        """Store deadlock pattern in VectorStore for learning."""
        from shared.agent_context import AgentContext

        context = AgentContext(session_id="deadlock_detection")
        await context.store_memory(
            key=f"deadlock_{datetime.now().isoformat()}",
            content={
                "type": "deadlock_detected",
                "cycle": [str(task) for task in cycle],
                "timestamp": datetime.now().isoformat(),
                "mitigation": "Lock ordering violated - use sorted acquisition"
            },
            tags=["memory_tool", "deadlock", "concurrency", "article_iv"]
        )
```

---

## 4. Error Handling Patterns

### 4.1 Async Exception Taxonomy

```python
class MemoryToolError(Exception):
    """Base exception for memory tool errors."""
    pass

class LockTimeoutError(MemoryToolError):
    """Lock acquisition timeout (potential deadlock)."""
    pass

class IOTimeoutError(MemoryToolError):
    """File I/O timeout (slow disk or large file)."""
    pass

class ValidationError(MemoryToolError):
    """Path validation failed (security)."""
    pass
```

### 4.2 Result Pattern Integration

```python
async def view_async(self, path: str) -> Result[str, MemoryToolError]:
    """Return Result instead of raising exceptions.

    Constitutional compliance: Explicit error handling (no try/catch control flow).
    """
    try:
        full_path = self._validate_path(path)
    except ValueError as e:
        return Err(ValidationError(str(e)))

    file_lock = await self._get_file_lock(full_path)

    try:
        async with asyncio.timeout(self.lock_timeout):
            await file_lock.acquire()
    except asyncio.TimeoutError:
        return Err(LockTimeoutError(f"Lock timeout: {path}"))

    try:
        content = await self._read_file_async(full_path)
        return Ok(content)
    except asyncio.TimeoutError:
        return Err(IOTimeoutError(f"I/O timeout: {path}"))
    except Exception as e:
        return Err(MemoryToolError(f"Unexpected: {e}"))
    finally:
        file_lock.release()
```

### 4.3 Retry with Exponential Backoff

```python
async def ensure_complete_context_async(
    operation: Callable[[], Awaitable[Result[T, E]]],
    max_retries: int = 3,
    base_timeout: float = 5.0
) -> Result[T, E]:
    """Article I compliance: Retry with exponential timeout.

    Timeout progression: 5s → 10s → 20s
    """
    timeout = base_timeout

    for attempt in range(max_retries):
        try:
            async with asyncio.timeout(timeout):
                result = await operation()

                if result.is_ok():
                    return result

                # Retry on error (unless it's a validation error)
                if isinstance(result.unwrap_err(), ValidationError):
                    return result  # Don't retry validation errors

        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                return Err(IOTimeoutError(f"Max retries ({max_retries}) exceeded"))

            timeout *= 2  # Exponential backoff
            continue

    return Err(MemoryToolError("Unreachable"))
```

---

## 5. Backward Compatibility

### 5.1 Sync Wrapper Pattern

```python
class MemoryTool(BetaAbstractMemoryTool):
    """Synchronous wrapper over AsyncMemoryTool.

    Maintains backward compatibility with existing sync callers.
    Uses asyncio.run() to execute async operations in sync context.
    """

    def __init__(self, *args, **kwargs):
        self._async_tool = AsyncMemoryTool(*args, **kwargs)
        self._loop = None

    def _run_async(self, coro):
        """Execute async coroutine in sync context."""
        try:
            # Use existing event loop if available
            loop = asyncio.get_running_loop()
            # If we're already in an async context, raise error
            raise RuntimeError(
                "MemoryTool sync methods cannot be called from async context. "
                "Use AsyncMemoryTool instead."
            )
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            return asyncio.run(coro)

    def view(self, path: str, view_range: list[int] | None = None) -> str:
        """Sync wrapper over view_async."""
        result = self._run_async(self._async_tool.view_async(path, view_range))

        if result.is_ok():
            return result.unwrap()
        else:
            # Return error string (matches current API)
            return f"Error: {result.unwrap_err()}"

    def create(self, path: str, file_text: str) -> str:
        """Sync wrapper over create_async."""
        result = self._run_async(self._async_tool.create_async(path, file_text))

        if result.is_ok():
            return result.unwrap()
        else:
            return f"Error: {result.unwrap_err()}"

    # ... similar wrappers for str_replace, insert, delete, rename
```

### 5.2 Migration Path

**Phase 1: Deprecation (Week 1-2)**
- Add `AsyncMemoryTool` alongside existing `AgencyMemoryTool`
- Update documentation to prefer async API
- Add deprecation warnings to sync API

**Phase 2: Gradual Migration (Week 3-4)**
- Migrate high-throughput callers (AgentContext, SwarmMemory)
- Update tests to use async API
- Maintain sync wrapper for compatibility

**Phase 3: Full Transition (Week 5+)**
- All internal Agency code uses async API
- Sync wrapper marked as legacy (kept for external users)
- Performance benchmarks validate 3x improvement

---

## 6. Performance Optimization

### 6.1 Parallel Read Strategy

**Current (Sequential):**
```python
# Reading 100 files: 100 * 5ms = 500ms
results = []
for path in paths:
    results.append(memory_tool.view(path))
```

**Optimized (Parallel):**
```python
# Reading 100 files with batch_view_async: ~50ms (10x concurrency)
results = await memory_tool.batch_view_async(paths, max_concurrency=10)
```

**Benchmark Target:**
- Sequential: 500ms (100 files * 5ms)
- Parallel: 50ms (100 files / 10 concurrency * 5ms)
- **10x speedup** (limited by I/O concurrency)

### 6.2 Lock Contention Reduction

**Strategy 1: Lock-Free Reads (Future)**
- Use `aiorwlock.RWLock` for shared reads
- Multiple agents read same file without blocking

**Strategy 2: Lock Striping**
- Instead of 1 lock per file, use N locks (e.g., 100)
- Hash file path to lock: `lock_index = hash(path) % N`
- Reduces contention on hot files

**Strategy 3: Cache Reads**
- Add in-memory LRU cache for frequently read files
- Cache invalidation on write operations
- Reduces lock acquisition frequency

### 6.3 I/O Optimization

**Use aiofiles efficiently:**
```python
# BAD: Blocking read in async context
async def slow_read(path):
    with open(path) as f:  # BLOCKS event loop
        return f.read()

# GOOD: Non-blocking async read
async def fast_read(path):
    async with aiofiles.open(path) as f:
        return await f.read()  # Yields to event loop
```

**Batch writes:**
```python
# Write multiple files in parallel
files = {
    "/memories/file1.txt": "content1",
    "/memories/file2.txt": "content2",
    # ... 100 files
}

results = await memory_tool.batch_create_async(files, max_concurrency=5)
```

---

## 7. Testing Strategy

### 7.1 Async Test Patterns

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_concurrent_reads():
    """Test multiple agents reading same file simultaneously."""
    tool = AsyncMemoryTool()
    await tool.create_async("/memories/shared.txt", "shared content")

    # 10 concurrent reads
    tasks = [tool.view_async("/memories/shared.txt") for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # All should succeed with same content
    assert all(r.is_ok() for r in results)
    assert all(r.unwrap() == "shared content" for r in results)

@pytest.mark.asyncio
async def test_lock_timeout():
    """Test lock timeout detection."""
    tool = AsyncMemoryTool(lock_timeout=0.1)

    # Agent 1 holds lock
    lock = await tool._get_file_lock(Path("/memories/test.txt"))
    await lock.acquire()

    # Agent 2 times out
    result = await tool.view_async("/memories/test.txt")
    assert result.is_err()
    assert "Lock timeout" in str(result.unwrap_err())

    lock.release()

@pytest.mark.asyncio
async def test_deadlock_prevention():
    """Test lock ordering prevents deadlock."""
    tool = AsyncMemoryTool()
    await tool.create_async("/memories/a.txt", "a")
    await tool.create_async("/memories/b.txt", "b")

    async def agent1():
        # Rename a → b (locks a, then b)
        return await tool.rename_async("/memories/a.txt", "/memories/b_new.txt")

    async def agent2():
        # Rename b → a (should also lock in sorted order: a, then b)
        return await tool.rename_async("/memories/b.txt", "/memories/a_new.txt")

    # No deadlock - both succeed (one fails due to file not found, but no hang)
    results = await asyncio.gather(agent1(), agent2(), return_exceptions=True)
    assert len(results) == 2
    assert not any(isinstance(r, asyncio.TimeoutError) for r in results)
```

### 7.2 Security Regression Tests

**All 30 existing security tests must pass:**
```bash
pytest tests/test_anthropic_memory_security.py -v
```

**Key test categories:**
1. Path traversal prevention (10 tests)
2. File size limits (3 tests)
3. Root directory protection (2 tests)
4. Symlink escape prevention (1 test)
5. Unicode handling (1 test)
6. Edge cases (13 tests)

**Async-specific security tests:**
```python
@pytest.mark.asyncio
async def test_async_path_traversal_blocked():
    """Async API blocks path traversal like sync API."""
    tool = AsyncMemoryTool()
    result = await tool.view_async("/memories/../etc/passwd")
    assert result.is_err()
    assert "traversal" in str(result.unwrap_err())

@pytest.mark.asyncio
async def test_concurrent_writes_atomic():
    """Concurrent writes to same file are atomic (no corruption)."""
    tool = AsyncMemoryTool()

    async def write_pattern(pattern: str, count: int):
        for i in range(count):
            await tool.create_async("/memories/shared.txt", pattern * 100)

    # 5 agents writing different patterns
    tasks = [
        write_pattern("A", 10),
        write_pattern("B", 10),
        write_pattern("C", 10),
        write_pattern("D", 10),
        write_pattern("E", 10),
    ]

    await asyncio.gather(*tasks)

    # Final content should be valid (all A's, all B's, etc.)
    result = await tool.view_async("/memories/shared.txt")
    assert result.is_ok()
    content = result.unwrap()

    # Check no corruption (content is homogeneous)
    assert all(c == content[0] for c in content)
```

### 7.3 Performance Benchmarks

```python
import time
import asyncio
import pytest

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_batch_view_speedup():
    """Validate 3x speedup with batch_view_async."""
    tool = AsyncMemoryTool()

    # Setup: 100 files
    files = {f"/memories/file{i}.txt": f"content{i}" for i in range(100)}
    await tool.batch_create_async(files)

    # Benchmark 1: Sequential
    start = time.perf_counter()
    for path in files.keys():
        await tool.view_async(path)
    sequential_time = time.perf_counter() - start

    # Benchmark 2: Parallel
    start = time.perf_counter()
    await tool.batch_view_async(list(files.keys()), max_concurrency=10)
    parallel_time = time.perf_counter() - start

    # Validate speedup
    speedup = sequential_time / parallel_time
    assert speedup >= 3.0, f"Expected 3x speedup, got {speedup:.2f}x"

    print(f"Sequential: {sequential_time:.3f}s")
    print(f"Parallel: {parallel_time:.3f}s")
    print(f"Speedup: {speedup:.2f}x")
```

---

## 8. Implementation Checklist

**Phase 1: Core Async Conversion (Days 1-3)**
- [ ] Create `AsyncMemoryTool` class with async init
- [ ] Implement `_get_file_lock()` with registry
- [ ] Convert `view()` → `view_async()` with aiofiles
- [ ] Convert `create()` → `create_async()` with atomic write
- [ ] Convert `str_replace()` → `str_replace_async()`
- [ ] Convert `insert()` → `insert_async()`
- [ ] Convert `delete()` → `delete_async()`
- [ ] Convert `rename()` → `rename_async()` with dual locks

**Phase 2: Concurrency Control (Days 4-5)**
- [ ] Implement `_acquire_multiple_locks()` for deadlock prevention
- [ ] Add lock timeout with `asyncio.timeout()`
- [ ] Implement `DeadlockDetector` with cycle detection
- [ ] Add telemetry for lock contention metrics
- [ ] Store deadlock patterns in VectorStore (Article IV)

**Phase 3: Batch Operations (Days 6-7)**
- [ ] Implement `batch_view_async()` with semaphore
- [ ] Implement `batch_create_async()` with lower concurrency
- [ ] Add `batch_str_replace_async()` for bulk edits
- [ ] Benchmark batch operations (3x speedup target)

**Phase 4: Error Handling (Day 8)**
- [ ] Define exception hierarchy (`LockTimeoutError`, `IOTimeoutError`)
- [ ] Integrate `Result<T, E>` pattern
- [ ] Implement `ensure_complete_context_async()` retry logic
- [ ] Add exponential backoff for transient errors

**Phase 5: Backward Compatibility (Day 9)**
- [ ] Create `MemoryTool` sync wrapper
- [ ] Implement `_run_async()` helper
- [ ] Test sync wrapper with existing callers
- [ ] Add deprecation warnings

**Phase 6: Testing (Days 10-12)**
- [ ] Migrate 30 security tests to async
- [ ] Add 10 concurrency tests (deadlock, race conditions)
- [ ] Add 5 performance benchmarks (speedup validation)
- [ ] Run full test suite: `pytest tests/ -v --asyncio-mode=auto`

**Phase 7: Integration (Days 13-14)**
- [ ] Update `AgentContext` to use `AsyncMemoryTool`
- [ ] Update `SwarmMemory` for async operations
- [ ] Update SDK integration (`anthropic_agent_with_memory.py`)
- [ ] Performance validation: 3x throughput improvement

**Phase 8: Documentation (Day 15)**
- [ ] Update `docs/ANTHROPIC_MEMORY_TOOL.md` with async examples
- [ ] Add async migration guide
- [ ] Update `CLAUDE.md` quick reference
- [ ] Create `plans/leap_2_memory_async_plan.md`

---

## 9. Success Metrics

**Performance:**
- ✅ 3x throughput improvement on parallel reads (batch_view_async)
- ✅ <5ms lock acquisition latency (99th percentile)
- ✅ <10ms I/O timeout on local disk
- ✅ Zero deadlocks in 10K concurrent operations

**Quality:**
- ✅ 100% test pass rate (30 security + 10 concurrency + 5 benchmark)
- ✅ Zero security regressions
- ✅ Backward compatibility maintained (sync wrapper)
- ✅ Type safety: strict mypy compliance

**Constitutional:**
- ✅ Article I: Retry logic with 2x, 3x, 10x timeout progression
- ✅ Article II: Atomic writes, no partial data
- ✅ Article III: CI validation with async tests
- ✅ Article IV: Deadlock patterns stored in VectorStore
- ✅ Article V: All code traces to this spec

---

## 10. Risks and Mitigations

### Risk 1: Deadlock in Multi-Agent Scenarios
**Likelihood:** Medium
**Impact:** High (blocking operations)
**Mitigation:**
- Global lock ordering (alphabetical path sorting)
- Lock timeout detection (5s default)
- Deadlock cycle logging to VectorStore

### Risk 2: Async/Sync Mixing Issues
**Likelihood:** High
**Impact:** Medium (runtime errors)
**Mitigation:**
- Clear API separation (`AsyncMemoryTool` vs `MemoryTool`)
- Runtime detection of async context in sync wrapper
- Comprehensive testing of both APIs

### Risk 3: Performance Regression
**Likelihood:** Low
**Impact:** Medium (slower than sync)
**Mitigation:**
- Benchmark suite validates 3x improvement
- Lock contention monitoring
- Fallback to sync API if degradation detected

### Risk 4: Security Regression
**Likelihood:** Low
**Impact:** Critical (path traversal vulnerability)
**Mitigation:**
- All 30 security tests ported to async
- Path validation remains synchronous (no async gap)
- Security audit before merge

---

## 11. Future Enhancements

### Phase 2: Read-Write Locks (Leap 3)
- Use `aiorwlock` for true shared reads
- 10x read throughput improvement (100 concurrent readers)

### Phase 3: Distributed Locks (Leap 4)
- Redis-backed locks for multi-node Agency
- Cross-machine coordination

### Phase 4: Event-Driven Notifications (Leap 5)
- File watch with `asyncio` + `watchdog`
- Reactive memory updates across agents

---

## 12. References

**ADRs:**
- ADR-001: Complete Context Before Action (retry logic)
- ADR-002: 100% Verification and Stability (atomic writes)
- ADR-004: Continuous Learning (deadlock pattern storage)

**Specs:**
- `specs/leap_2_memory_analysis.md` - Current architecture
- `specs/leap_2_vectorstore_optimization.md` - VectorStore integration

**Implementation:**
- `tools/anthropic_memory_tool.py` - Current sync implementation
- `trinity_protocol/core/hybrid_executor.py` - Async pattern reference
- `shared/message_bus.py` - Async message queue pattern

**Tests:**
- `tests/test_anthropic_memory_security.py` - 30 security tests

---

## Appendix A: Async Pattern Examples

### Example 1: Agent Memory Write
```python
async def agent_workflow():
    """Example: Agent writes to memory during task."""
    from tools.anthropic_memory_tool import AsyncMemoryTool

    memory = AsyncMemoryTool(session_id="agent_123")

    # Write task progress
    result = await memory.create_async(
        "/memories/tasks/current.md",
        "# Task Progress\n\n- [x] Step 1\n- [ ] Step 2"
    )

    if result.is_err():
        print(f"Error: {result.unwrap_err()}")
        return

    print(result.unwrap())  # "Successfully created: /memories/tasks/current.md (45 chars)"
```

### Example 2: Multi-Agent Batch Read
```python
async def swarm_coordination():
    """Example: 10 agents read shared knowledge base."""
    from tools.anthropic_memory_tool import AsyncMemoryTool

    memory = AsyncMemoryTool()

    # All agents read documentation in parallel
    docs = [
        "/memories/docs/api_guide.md",
        "/memories/docs/architecture.md",
        "/memories/docs/patterns.md",
        # ... 100 docs
    ]

    results = await memory.batch_view_async(docs, max_concurrency=10)

    for path, result in results.items():
        if result.is_ok():
            content = result.unwrap()
            print(f"Read {path}: {len(content)} bytes")
        else:
            print(f"Failed {path}: {result.unwrap_err()}")
```

### Example 3: Retry with Timeout
```python
async def robust_memory_access():
    """Example: Article I compliance with retry."""
    from tools.anthropic_memory_tool import AsyncMemoryTool, ensure_complete_context_async

    memory = AsyncMemoryTool()

    async def read_critical_data():
        return await memory.view_async("/memories/critical/data.json")

    # Retry with exponential backoff: 5s → 10s → 20s
    result = await ensure_complete_context_async(
        read_critical_data,
        max_retries=3,
        base_timeout=5.0
    )

    if result.is_ok():
        data = result.unwrap()
        print(f"Success: {data}")
    else:
        print(f"Failed after 3 retries: {result.unwrap_err()}")
```

---

**Spec Version:** 1.0
**Last Updated:** 2025-10-10
**Next Review:** After Phase 1 implementation (Day 3)
**Owner:** ChiefArchitect
**Stakeholders:** AgencyCodeAgent, QualityEnforcer, LearningAgent
