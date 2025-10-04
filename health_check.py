#!/usr/bin/env python3
"""
Agency OS Health Check Script
Quick validation that the system is properly configured and operational
"""

import os
import subprocess
import sys
from pathlib import Path

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check_mark(passed: bool) -> str:
    return f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"


def print_header(title: str):
    print(f"\n{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}")


def check_python_version() -> tuple[bool, str]:
    """Check if Python version is 3.12 or 3.13"""
    import sys

    version = sys.version_info
    if version.major == 3 and version.minor in [12, 13]:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (3.12 or 3.13 required)"


def check_virtual_env() -> tuple[bool, str]:
    """Check if running in a virtual environment"""
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        return True, f"Virtual environment: {sys.prefix}"
    return False, "Not in virtual environment (recommended)"


def check_env_file() -> tuple[bool, str]:
    """Check if .env file exists and has required keys"""
    if not os.path.exists(".env"):
        return False, ".env file not found (copy from .env.example)"

    with open(".env") as f:
        content = f.read()
        if "OPENAI_API_KEY" not in content:
            return False, ".env exists but missing OPENAI_API_KEY"

    return True, ".env file configured"


def check_dependencies() -> tuple[bool, str]:
    """Check if key dependencies are installed"""
    try:
        import agency_swarm
        import pytest
        import ruff

        return True, "Core dependencies installed"
    except ImportError as e:
        missing = str(e).split("'")[1]
        return False, f"Missing dependency: {missing}"


def check_test_health() -> tuple[bool, str]:
    """Run a quick test to check system health"""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-x", "--maxfail=1", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, "Quick test passed"
        else:
            # Count failures in output
            failures = result.stdout.count("FAILED")
            return False, f"Quick test failed ({failures} failures)"
    except subprocess.TimeoutExpired:
        return False, "Tests timed out"
    except Exception as e:
        return False, f"Test error: {str(e)}"


def check_directories() -> tuple[bool, str]:
    """Check if required directories exist"""
    required_dirs = [
        "logs/sessions",
        "logs/telemetry",
        "specs",
        "plans",
        ".claude/commands",
        ".claude/agents",
    ]

    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)

    if missing:
        return False, f"Missing directories: {', '.join(missing)}"
    return True, "All required directories present"


def check_constitutional_compliance() -> tuple[bool, str]:
    """Check if constitutional compliance script exists"""
    script_path = "scripts/constitutional_check.py"
    if not Path(script_path).exists():
        return False, "Constitutional check script not found"

    try:
        result = subprocess.run(["python", script_path], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, "Constitutional compliance verified"
        return False, "Constitutional compliance check failed"
    except Exception:
        return False, "Could not run constitutional check"


def check_agents() -> tuple[bool, str]:
    """Check if agent modules are accessible"""
    agent_modules = [
        "agency_code_agent",
        "planner_agent",
        "auditor_agent",
        "quality_enforcer_agent",
        "chief_architect_agent",
    ]

    missing = []
    for module in agent_modules:
        if not Path(module).exists():
            missing.append(module)

    if missing:
        return False, f"Missing agents: {', '.join(missing)}"
    return True, f"All {len(agent_modules)} core agents present"


def main():
    print_header("Agency OS Health Check")

    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_env),
        ("Environment Config", check_env_file),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directories),
        ("Agent Modules", check_agents),
        ("Constitutional Check", check_constitutional_compliance),
        ("Test Health", check_test_health),
    ]

    results = []
    for name, check_func in checks:
        try:
            passed, message = check_func()
            results.append(passed)
            print(f"{check_mark(passed)} {name}: {message}")
        except Exception as e:
            results.append(False)
            print(f"{check_mark(False)} {name}: Error - {str(e)}")

    # Summary
    print_header("Summary")
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"{GREEN}✅ All checks passed! ({passed}/{total}){RESET}")
        print(f"\n{GREEN}Agency OS is healthy and ready for operation.{RESET}")
        print("\nNext steps:")
        print("1. Run 'python agency.py' to start")
        print("2. Use /prime commands for autonomous development")
        print("3. Run 'make test-all' for full validation")
        return 0
    else:
        print(f"{YELLOW}⚠️  Some checks failed ({passed}/{total}){RESET}")
        print(f"\n{YELLOW}Agency OS needs attention. Please fix the issues above.{RESET}")
        print("\nQuick fixes:")
        print("1. Run './setup_dev.sh' to set up environment")
        print("2. Copy .env.example to .env and add API keys")
        print("3. Run 'make setup' for complete setup")
        return 1


if __name__ == "__main__":
    sys.exit(main())
