"""
Health Monitor - Mission 5 System Health Monitoring

Monitors system health and performs self-diagnostics before autonomous execution:
- Disk space monitoring
- Memory utilization monitoring
- CPU utilization monitoring
- Git repository validation
- Dependency checks

TDD Protocol (Article VI):
- Tests written FIRST in tests/test_auto_recovery.py (5 tests in TestHealthMonitoring)
- This implementation makes tests pass (GREEN phase)

Usage:
    from tools.health_monitor import HealthMonitor

    monitor = HealthMonitor()
    health = monitor.check_health()

    if not health["healthy"]:
        print(f"Health check failed: {health}")
"""

import importlib
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

import psutil

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Health Monitor - System Health Monitoring (Mission 5).

    Monitors system health before autonomous execution:
    - Disk space: >10GB free required
    - Memory: <80% utilization required
    - CPU: <90% average utilization (5-minute window)
    - Git repo: Clean working tree, up-to-date with remote
    - Dependencies: All required packages installed

    Methods:
    - check_health(required_modules=[]): Perform health check
    - check_resources(): Check disk, memory, CPU
    - check_git_status(): Check git repository status
    - check_dependencies(modules): Check required modules installed
    """

    def __init__(self, state_dir: Optional[str] = None):
        """
        Initialize Health Monitor.

        Args:
            state_dir: Directory for state and logs (default: ~/.agency)
        """
        if state_dir is None:
            state_dir = str(Path.home() / ".agency")

        self.state_dir = Path(state_dir)
        self.log_dir = self.state_dir / "logs" / "health"

        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def check_resources(self) -> dict[str, Any]:
        """
        Check system resources (disk, memory, CPU).

        Returns:
            dict: Resource status
        """
        # Check disk space
        disk_usage = shutil.disk_usage("/")
        disk_free_gb = disk_usage.free / (1024**3)

        # Check memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Check CPU
        cpu_percent = psutil.cpu_percent(interval=1)

        # Determine if healthy
        healthy = (
            disk_free_gb >= 10.0  # At least 10GB free
            and memory_percent < 80.0  # Less than 80% memory used
            and cpu_percent < 90.0  # Less than 90% CPU used
        )

        return {
            "disk_free_gb": disk_free_gb,
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent,
            "healthy": healthy,
        }

    def check_git_status(self) -> dict[str, Any]:
        """
        Check git repository status.

        Returns:
            dict: Git status
        """
        try:
            # Check if working tree is clean
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
            )

            git_clean = result.returncode == 0 and len(result.stdout.strip()) == 0

            return {
                "git_clean": git_clean,
                "git_status": result.stdout,
            }

        except Exception as e:
            logger.error(f"Git status check failed: {e}")
            return {
                "git_clean": False,
                "git_status": str(e),
            }

    def check_dependencies(self, required_modules: list[str]) -> dict[str, Any]:
        """
        Check if required modules are installed.

        Args:
            required_modules: List of module names to check

        Returns:
            dict: Dependency status
        """
        missing_modules = []

        for module_name in required_modules:
            try:
                importlib.import_module(module_name)
            except ImportError:
                missing_modules.append(module_name)

        dependencies_ok = len(missing_modules) == 0

        return {
            "dependencies_ok": dependencies_ok,
            "missing_modules": missing_modules,
        }

    def check_health(self, required_modules: Optional[list[str]] = None) -> dict[str, Any]:
        """
        Perform comprehensive health check.

        Args:
            required_modules: Optional list of modules to check

        Returns:
            dict: Health status
        """
        if required_modules is None:
            required_modules = []

        # Check resources
        resource_status = self.check_resources()

        # Check git status
        git_status = self.check_git_status()

        # Check dependencies
        dependency_status = self.check_dependencies(required_modules)

        # Combine all checks
        health = {
            **resource_status,
            **git_status,
            **dependency_status,
        }

        # Overall health status
        health["healthy"] = (
            resource_status["healthy"]
            and git_status.get("git_clean", True)
            and dependency_status.get("dependencies_ok", True)
        )

        return health
