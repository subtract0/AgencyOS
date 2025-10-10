"""
Performance benchmarks for session compression, GC, and checkpoints.

Validates performance targets from specification:
- Compression: <10ms for 1MB sessions
- GC: <100ms for 1000 sessions
- Checkpoint: <10ms save/load

Constitutional Compliance:
- Article II: 100% test pass (performance within spec)
- Article V: Trace to spec (leap_2_session_state_optimization.md)

Specification: specs/leap_2_session_state_optimization.md
Performance Targets:
- AC-P.1: Session save <10ms for 1MB
- AC-P.2: Session load <8ms for 1MB compressed
- AC-P.3: GC scan rate 100+ sessions/second
- AC-P.4: Checkpoint overhead <5ms vs full save
"""

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from shared.models.session import SessionState, SessionStatus
from shared.session_checkpoint import SessionCheckpointManager
from shared.session_compression import compress_session_state, decompress_session_state
from shared.session_gc import SessionGarbageCollector


class TestCompressionPerformance:
    """Benchmark compression performance (AC-P.1, AC-P.2)."""

    def test_benchmark_compression_1mb(self):
        """Benchmark compression <10ms for 1MB session (AC-P.1)."""
        # Arrange - Create 1MB session
        large_metadata = {f"key_{i}": "x" * 1000 for i in range(1000)}
        session = SessionState(
            session_id="benchmark_1mb",
            agent_name="benchmark",
            metadata=large_metadata,
        )

        # Act - Compress 10 times and average
        times = []
        for _ in range(10):
            start = time.perf_counter()
            result = compress_session_state(session)
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
            assert result.is_ok()

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        # Assert
        print(f"\nCompression 1MB: avg={avg_time:.2f}ms, min={min_time:.2f}ms, max={max_time:.2f}ms")
        assert avg_time < 10.0, f"Average compression time {avg_time:.2f}ms exceeds 10ms target (AC-P.1)"

    def test_benchmark_decompression_1mb(self):
        """Benchmark decompression <8ms for 1MB compressed session (AC-P.2)."""
        # Arrange - Compress 1MB session
        large_metadata = {f"key_{i}": "x" * 1000 for i in range(1000)}
        session = SessionState(
            session_id="benchmark_decompress_1mb",
            agent_name="benchmark",
            metadata=large_metadata,
        )
        compress_result = compress_session_state(session)
        assert compress_result.is_ok()
        compressed, _ = compress_result.unwrap()

        # Act - Decompress 10 times and average
        times = []
        for _ in range(10):
            start = time.perf_counter()
            result = decompress_session_state(compressed)
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
            assert result.is_ok()

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        # Assert
        print(f"\nDecompression 1MB: avg={avg_time:.2f}ms, min={min_time:.2f}ms, max={max_time:.2f}ms")
        assert avg_time < 8.0, f"Average decompression time {avg_time:.2f}ms exceeds 8ms target (AC-P.2)"

    def test_benchmark_compression_ratio_1mb(self):
        """Benchmark compression ratio for 1MB session."""
        # Arrange - Create 1MB session with typical data
        large_metadata = {f"key_{i}": f"value_{i % 10}" * 100 for i in range(1000)}  # Repetitive
        session = SessionState(
            session_id="benchmark_ratio",
            agent_name="benchmark",
            metadata=large_metadata,
        )

        # Act
        result = compress_session_state(session)
        assert result.is_ok()
        _, metadata = result.unwrap()

        # Assert
        print(f"\nCompression ratio: {metadata.compression_ratio:.4f} "
              f"(reduction: {metadata.size_reduction_percent:.1f}%)")
        print(f"  Original: {metadata.original_size_bytes:,} bytes")
        print(f"  Compressed: {metadata.compressed_size_bytes:,} bytes")
        assert metadata.size_reduction_percent >= 60.0

    def test_benchmark_compression_levels(self):
        """Benchmark compression levels 1-9 for speed vs ratio trade-off."""
        # Arrange
        session = SessionState(
            session_id="level_benchmark",
            agent_name="benchmark",
            metadata={f"key_{i}": "x" * 100 for i in range(100)},
        )

        # Act - Test all compression levels
        print("\nCompression level benchmarks:")
        print("Level | Time (ms) | Ratio   | Reduction")
        print("------|-----------|---------|----------")

        for level in range(1, 10):
            start = time.perf_counter()
            result = compress_session_state(session, compression_level=level)
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert result.is_ok()
            _, metadata = result.unwrap()

            print(f"  {level}   | {elapsed_ms:7.2f}   | {metadata.compression_ratio:6.4f}  | "
                  f"{metadata.size_reduction_percent:5.1f}%")

        # Assert - Level 6 (default) should be balanced
        result = compress_session_state(session, compression_level=6)
        assert result.is_ok()
        _, metadata = result.unwrap()
        assert metadata.compression_time_ms < 5.0  # Fast enough
        assert metadata.size_reduction_percent > 50.0  # Good compression


class TestGarbageCollectionPerformance:
    """Benchmark GC performance (AC-P.3)."""

    @pytest.fixture
    def temp_session_dir(self, tmp_path):
        """Create temporary session directory."""
        session_dir = tmp_path / "perf_sessions"
        session_dir.mkdir()
        return session_dir

    @pytest.fixture
    def temp_archive_dir(self, tmp_path):
        """Create temporary archive directory."""
        archive_dir = tmp_path / "perf_archives"
        archive_dir.mkdir()
        return archive_dir

    def test_benchmark_gc_1000_sessions(self, temp_session_dir, temp_archive_dir):
        """Benchmark GC scan rate 100+ sessions/second (AC-P.3)."""
        # Arrange - Create 1000 session files
        for i in range(1000):
            session = SessionState(
                session_id=f"perf_session_{i:04d}",
                agent_name="benchmark",
                status=SessionStatus.COMPLETED if i % 2 == 0 else SessionStatus.PENDING,
                created_at=datetime.now() - timedelta(days=i % 100),
                updated_at=datetime.now() - timedelta(days=i % 100),
            )
            session_file = temp_session_dir / f"{session.session_id}.json"
            session_file.write_text(session.model_dump_json())

        collector = SessionGarbageCollector(
            session_dir=temp_session_dir,
            archive_dir=temp_archive_dir,
        )

        # Act - Run GC with dry-run
        start = time.perf_counter()
        result = collector.collect_expired_sessions(dry_run=True)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert result.is_ok()
        gc_metrics = result.unwrap()

        sessions_per_second = (gc_metrics.sessions_scanned / elapsed_ms) * 1000
        print("\nGC Performance:")
        print(f"  Sessions scanned: {gc_metrics.sessions_scanned}")
        print(f"  Time: {elapsed_ms:.2f}ms")
        print(f"  Rate: {sessions_per_second:.0f} sessions/second")

        assert sessions_per_second >= 100, (
            f"GC scan rate {sessions_per_second:.0f} sessions/sec < 100 target (AC-P.3)"
        )

    def test_benchmark_gc_with_deletion(self, temp_session_dir, temp_archive_dir):
        """Benchmark GC with actual deletion (not dry-run)."""
        # Arrange - Create 100 expired sessions
        for i in range(100):
            session = SessionState(
                session_id=f"delete_session_{i:03d}",
                agent_name="benchmark",
                status=SessionStatus.EXPIRED,
                created_at=datetime.now() - timedelta(days=31),
                updated_at=datetime.now() - timedelta(days=31),
            )
            session_file = temp_session_dir / f"{session.session_id}.json"
            session_file.write_text(session.model_dump_json())

        collector = SessionGarbageCollector(
            session_dir=temp_session_dir,
            archive_dir=temp_archive_dir,
        )

        # Act - Run GC with actual deletion
        start = time.perf_counter()
        result = collector.collect_expired_sessions(dry_run=False)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert result.is_ok()
        gc_metrics = result.unwrap()

        print("\nGC with deletion:")
        print(f"  Sessions deleted: {gc_metrics.sessions_deleted}")
        print(f"  Time: {elapsed_ms:.2f}ms")
        print(f"  Disk space reclaimed: {gc_metrics.disk_space_reclaimed_mb:.2f}MB")

        assert gc_metrics.sessions_deleted == 100
        assert elapsed_ms < 1000  # <1 second for 100 deletions


class TestCheckpointPerformance:
    """Benchmark checkpoint performance (AC-P.4)."""

    @pytest.fixture
    def temp_checkpoint_dir(self, tmp_path):
        """Create temporary checkpoint directory."""
        checkpoint_dir = tmp_path / "perf_checkpoints"
        checkpoint_dir.mkdir()
        return checkpoint_dir

    def test_benchmark_checkpoint_save_load(self, temp_checkpoint_dir):
        """Benchmark checkpoint save/load <10ms (AC-P.4)."""
        # Arrange
        manager = SessionCheckpointManager(temp_checkpoint_dir)
        session = SessionState(
            session_id="checkpoint_perf",
            agent_name="benchmark",
            metadata={"data": "x" * 10000},
        )

        # Act - Save checkpoint
        save_times = []
        for i in range(10):
            start = time.perf_counter()
            result = manager.save_checkpoint(
                session=session,
                step_name=f"step_{i}",
                completed_steps=[],
                pending_steps=[],
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            save_times.append(elapsed_ms)
            assert result.is_ok()
            time.sleep(0.01)  # Ensure different timestamps

        # Act - Resume checkpoints
        checkpoints = manager.list_checkpoints("checkpoint_perf")
        resume_times = []
        for checkpoint_id in checkpoints:
            start = time.perf_counter()
            result = manager.resume_from_checkpoint(checkpoint_id)
            elapsed_ms = (time.perf_counter() - start) * 1000
            resume_times.append(elapsed_ms)
            assert result.is_ok()

        # Assert
        avg_save = sum(save_times) / len(save_times)
        avg_resume = sum(resume_times) / len(resume_times)

        print("\nCheckpoint Performance:")
        print(f"  Save:   avg={avg_save:.2f}ms, min={min(save_times):.2f}ms, max={max(save_times):.2f}ms")
        print(f"  Resume: avg={avg_resume:.2f}ms, min={min(resume_times):.2f}ms, max={max(resume_times):.2f}ms")

        assert avg_save < 10.0, f"Average save time {avg_save:.2f}ms exceeds 10ms target"
        assert avg_resume < 10.0, f"Average resume time {avg_resume:.2f}ms exceeds 10ms target"

    def test_benchmark_checkpoint_overhead(self, temp_checkpoint_dir):
        """Benchmark checkpoint overhead vs full save (AC-P.4)."""
        # Arrange
        manager = SessionCheckpointManager(temp_checkpoint_dir)
        session = SessionState(
            session_id="overhead_test",
            agent_name="benchmark",
            metadata={"data": "x" * 10000},
        )

        # Act - Time full save (compression only)
        compress_times = []
        for _ in range(10):
            start = time.perf_counter()
            result = compress_session_state(session)
            elapsed_ms = (time.perf_counter() - start) * 1000
            compress_times.append(elapsed_ms)
            assert result.is_ok()

        # Act - Time checkpoint save (compression + checkpoint metadata)
        checkpoint_times = []
        for i in range(10):
            start = time.perf_counter()
            result = manager.save_checkpoint(
                session=session,
                step_name=f"overhead_{i}",
                completed_steps=[],
                pending_steps=[],
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            checkpoint_times.append(elapsed_ms)
            assert result.is_ok()
            time.sleep(0.01)

        # Assert
        avg_compress = sum(compress_times) / len(compress_times)
        avg_checkpoint = sum(checkpoint_times) / len(checkpoint_times)
        overhead_ms = avg_checkpoint - avg_compress

        print("\nCheckpoint Overhead:")
        print(f"  Compression only: {avg_compress:.2f}ms")
        print(f"  With checkpoint:  {avg_checkpoint:.2f}ms")
        print(f"  Overhead:         {overhead_ms:.2f}ms")

        assert overhead_ms < 5.0, (
            f"Checkpoint overhead {overhead_ms:.2f}ms exceeds 5ms target (AC-P.4)"
        )


class TestEndToEndPerformance:
    """Benchmark complete workflows."""

    def test_benchmark_full_session_lifecycle(self, tmp_path):
        """Benchmark complete session lifecycle."""
        # Setup
        checkpoint_dir = tmp_path / "lifecycle_checkpoints"
        checkpoint_dir.mkdir()
        manager = SessionCheckpointManager(checkpoint_dir)

        session = SessionState(
            session_id="lifecycle_perf",
            agent_name="benchmark",
            metadata={"data": "x" * 10000},
        )

        # Benchmark lifecycle
        times = {}

        # Step 1: Compress
        start = time.perf_counter()
        compress_result = compress_session_state(session)
        times["compress"] = (time.perf_counter() - start) * 1000
        assert compress_result.is_ok()
        compressed, _ = compress_result.unwrap()

        # Step 2: Decompress
        start = time.perf_counter()
        decompress_result = decompress_session_state(compressed)
        times["decompress"] = (time.perf_counter() - start) * 1000
        assert decompress_result.is_ok()

        # Step 3: Checkpoint
        start = time.perf_counter()
        checkpoint_result = manager.save_checkpoint(
            session=session,
            step_name="benchmark",
            completed_steps=[],
            pending_steps=[],
        )
        times["checkpoint_save"] = (time.perf_counter() - start) * 1000
        assert checkpoint_result.is_ok()
        checkpoint_id = checkpoint_result.unwrap()

        # Step 4: Resume
        start = time.perf_counter()
        resume_result = manager.resume_from_checkpoint(checkpoint_id)
        times["checkpoint_resume"] = (time.perf_counter() - start) * 1000
        assert resume_result.is_ok()

        # Results
        total_time = sum(times.values())
        print("\nFull Lifecycle Benchmark:")
        for operation, time_ms in times.items():
            print(f"  {operation:18s}: {time_ms:6.2f}ms ({time_ms/total_time*100:5.1f}%)")
        print(f"  {'Total':18s}: {total_time:6.2f}ms")

        # Assert - Total lifecycle <50ms
        assert total_time < 50, f"Full lifecycle {total_time:.2f}ms exceeds 50ms target"

    def test_benchmark_memory_usage(self):
        """Benchmark memory footprint for 50 active sessions."""
        import sys

        # Arrange - Create 50 sessions
        sessions = []
        for i in range(50):
            session = SessionState(
                session_id=f"memory_session_{i:02d}",
                agent_name="benchmark",
                status=SessionStatus.RUNNING,
                metadata={"data": "x" * 1000},  # ~1KB per session
            )
            sessions.append(session)

        # Measure memory (approximate via JSON size)
        uncompressed_size = sum(len(s.model_dump_json().encode()) for s in sessions)

        # Compress all sessions
        compressed_sizes = []
        for session in sessions:
            result = compress_session_state(session)
            assert result.is_ok()
            compressed, metadata = result.unwrap()
            compressed_sizes.append(len(compressed))

        compressed_size = sum(compressed_sizes)

        # Results
        print("\nMemory Usage (50 sessions):")
        print(f"  Uncompressed: {uncompressed_size / (1024 * 1024):.2f}MB")
        print(f"  Compressed:   {compressed_size / (1024 * 1024):.2f}MB")
        print(f"  Reduction:    {(1 - compressed_size/uncompressed_size)*100:.1f}%")

        # Assert - <100MB total for 50 sessions with compression
        assert compressed_size / (1024 * 1024) < 100, "Memory footprint exceeds 100MB target"


class TestScalabilityBenchmarks:
    """Test scalability with increasing load."""

    def test_benchmark_compression_scalability(self):
        """Test compression performance with increasing session sizes."""
        sizes_kb = [1, 10, 100, 1000]  # 1KB to 1MB
        results = []

        print("\nCompression Scalability:")
        print("Size (KB) | Time (ms) | Ratio   | Throughput (MB/s)")
        print("----------|-----------|---------|------------------")

        for size_kb in sizes_kb:
            # Create session of specified size
            data_length = (size_kb * 1024) // 100  # Approximate
            session = SessionState(
                session_id=f"scale_{size_kb}kb",
                agent_name="benchmark",
                metadata={"data": "x" * data_length},
            )

            # Benchmark
            start = time.perf_counter()
            result = compress_session_state(session)
            elapsed = time.perf_counter() - start
            elapsed_ms = elapsed * 1000

            assert result.is_ok()
            _, metadata = result.unwrap()

            throughput_mbps = (metadata.original_size_bytes / (1024 * 1024)) / elapsed

            print(f"{size_kb:9d} | {elapsed_ms:9.2f} | {metadata.compression_ratio:6.4f}  | "
                  f"{throughput_mbps:16.2f}")

            results.append({
                "size_kb": size_kb,
                "time_ms": elapsed_ms,
                "ratio": metadata.compression_ratio,
                "throughput_mbps": throughput_mbps,
            })

        # Assert - Performance scales reasonably
        # Larger files should have similar or better throughput due to compression efficiency
        assert results[-1]["time_ms"] < 15.0  # 1MB should compress in <15ms

    def test_benchmark_gc_scalability(self, tmp_path):
        """Test GC performance with increasing session counts."""
        session_counts = [100, 500, 1000]
        results = []

        print("\nGC Scalability:")
        print("Sessions | Time (ms) | Rate (sess/sec)")
        print("---------|-----------|----------------")

        for count in session_counts:
            # Create sessions
            session_dir = tmp_path / f"gc_scale_{count}"
            session_dir.mkdir()

            for i in range(count):
                session = SessionState(
                    session_id=f"session_{i:04d}",
                    agent_name="benchmark",
                    status=SessionStatus.COMPLETED,
                )
                session_file = session_dir / f"{session.session_id}.json"
                session_file.write_text(session.model_dump_json())

            # Benchmark
            collector = SessionGarbageCollector(session_dir=session_dir)
            start = time.perf_counter()
            result = collector.collect_expired_sessions(dry_run=True)
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert result.is_ok()
            rate = (count / elapsed_ms) * 1000

            print(f"{count:8d} | {elapsed_ms:9.2f} | {rate:14.0f}")

            results.append({
                "count": count,
                "time_ms": elapsed_ms,
                "rate": rate,
            })

        # Assert - Rate should stay above 100 sessions/sec even at 1000 sessions
        assert results[-1]["rate"] >= 100
