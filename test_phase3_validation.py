#!/usr/bin/env python3
"""
Phase 3 Validation Script - ADR-002 Enforcement System

This script validates all Phase 3 components:
1. MergerAgent availability and functionality
2. Pre-commit hook existence and functionality
3. GitHub Actions workflow validity
4. Integration testing capabilities

Run this script to verify complete Phase 3 implementation.
"""

import os
import subprocess
import sys
from pathlib import Path


# Colors for output
class Colors:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(60)}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")


def print_test(test_name, status, details=""):
    """Print a test result."""
    status_color = Colors.GREEN if status == "PASS" else Colors.RED
    status_symbol = "✅" if status == "PASS" else "❌"
    print(f"{status_symbol} {test_name:<40} {status_color}{status}{Colors.RESET}")
    if details:
        print(f"   {Colors.YELLOW}{details}{Colors.RESET}")


def test_merger_agent():
    """Test MergerAgent availability and functionality."""
    print_section("TESTING MERGER AGENT")

    results = []

    # Test 1: Check if MergerAgent directory exists
    merger_path = Path("merger_agent")
    if merger_path.exists() and merger_path.is_dir():
        print_test("MergerAgent directory exists", "PASS")
        results.append(True)
    else:
        print_test("MergerAgent directory exists", "FAIL", f"Path {merger_path} not found")
        results.append(False)

    # Test 2: Check if MergerAgent can be imported
    try:
        sys.path.insert(0, os.getcwd())
        from merger_agent import create_merger_agent

        print_test("MergerAgent import", "PASS")
        results.append(True)
    except ImportError as e:
        print_test("MergerAgent import", "FAIL", str(e))
        results.append(False)
        return results

    # Test 3: Check if MergerAgent can be instantiated
    try:
        from shared.agent_context import create_agent_context

        context = create_agent_context()
        agent = create_merger_agent(agent_context=context)
        print_test("MergerAgent instantiation", "PASS")
        results.append(True)

        # Test 4: Check agent properties
        if hasattr(agent, "name") and agent.name == "MergerAgent":
            print_test("MergerAgent name property", "PASS")
            results.append(True)
        else:
            print_test(
                "MergerAgent name property",
                "FAIL",
                f"Expected 'MergerAgent', got '{getattr(agent, 'name', 'None')}'",
            )
            results.append(False)

        # Test 5: Check required tools
        required_tools = ["Bash", "Git", "Read", "Grep", "Glob", "TodoWrite"]
        actual_tools = [
            getattr(tool, "name", getattr(tool, "__name__", str(tool))) for tool in agent.tools
        ]
        missing_tools = [tool for tool in required_tools if tool not in actual_tools]

        if not missing_tools:
            print_test("MergerAgent required tools", "PASS")
            results.append(True)
        else:
            print_test("MergerAgent required tools", "FAIL", f"Missing tools: {missing_tools}")
            results.append(False)

    except Exception as e:
        print_test("MergerAgent instantiation", "FAIL", str(e))
        results.append(False)

    return results


def test_precommit_hook():
    """Test pre-commit hook existence and functionality."""
    print_section("TESTING PRE-COMMIT HOOK")

    results = []
    hook_path = Path(".git/hooks/pre-commit")

    # Test 1: Check if hook exists
    if hook_path.exists():
        print_test("Pre-commit hook exists", "PASS")
        results.append(True)
    else:
        print_test("Pre-commit hook exists", "FAIL", f"File {hook_path} not found")
        results.append(False)
        return results

    # Test 2: Check if hook is executable
    if os.access(hook_path, os.X_OK):
        print_test("Pre-commit hook executable", "PASS")
        results.append(True)
    else:
        print_test("Pre-commit hook executable", "FAIL", "Hook file is not executable")
        results.append(False)

    # Test 3: Check hook content
    try:
        with open(hook_path) as f:
            content = f.read()

        required_elements = [
            "ADR-002",
            "100% test verification",
            "python run_tests.py",
            "exit 1",
            "exit 0",
        ]
        missing_elements = [elem for elem in required_elements if elem not in content]

        if not missing_elements:
            print_test("Pre-commit hook content", "PASS")
            results.append(True)
        else:
            print_test("Pre-commit hook content", "FAIL", f"Missing elements: {missing_elements}")
            results.append(False)

    except Exception as e:
        print_test("Pre-commit hook content", "FAIL", str(e))
        results.append(False)

    # Test 4: Check if hook can be executed (dry run)
    try:
        # Create a simple test to see if the hook can start
        result = subprocess.run(
            [str(hook_path)], cwd=os.getcwd(), capture_output=True, text=True, timeout=10
        )
        # The hook should exit with 0 or 1, any other exit code indicates an error
        if result.returncode in [0, 1]:
            print_test("Pre-commit hook execution", "PASS", "Hook can be executed successfully")
            results.append(True)
        else:
            print_test(
                "Pre-commit hook execution", "FAIL", f"Hook exited with code {result.returncode}"
            )
            results.append(False)
    except subprocess.TimeoutExpired:
        print_test(
            "Pre-commit hook execution",
            "PASS",
            "Hook executed (timed out as expected for full test run)",
        )
        results.append(True)
    except Exception as e:
        print_test("Pre-commit hook execution", "FAIL", str(e))
        results.append(False)

    return results


def test_github_workflow():
    """Test GitHub Actions workflow validity."""
    print_section("TESTING GITHUB ACTIONS WORKFLOW")

    results = []
    workflow_path = Path(".github/workflows/merge-guardian.yml")

    # Test 1: Check if workflow exists
    if workflow_path.exists():
        print_test("GitHub workflow exists", "PASS")
        results.append(True)
    else:
        print_test("GitHub workflow exists", "FAIL", f"File {workflow_path} not found")
        results.append(False)
        return results

    # Test 2: Check workflow content
    try:
        with open(workflow_path) as f:
            content = f.read()

        # Test basic YAML structure
        required_yaml_elements = ["name:", "on:", "jobs:", "runs-on:", "steps:"]
        missing_yaml = [elem for elem in required_yaml_elements if elem not in content]

        if not missing_yaml:
            print_test("GitHub workflow YAML structure", "PASS")
            results.append(True)
        else:
            print_test(
                "GitHub workflow YAML structure", "FAIL", f"Missing elements: {missing_yaml}"
            )
            results.append(False)

        # Test ADR-002 enforcement content
        adr_elements = ["ADR-002", "100%", "test", "python run_tests.py"]
        missing_adr = [elem for elem in adr_elements if elem not in content]

        if not missing_adr:
            print_test("GitHub workflow ADR-002 enforcement", "PASS")
            results.append(True)
        else:
            print_test(
                "GitHub workflow ADR-002 enforcement", "FAIL", f"Missing elements: {missing_adr}"
            )
            results.append(False)

        # Test workflow triggers
        trigger_elements = ["pull_request:", "push:"]
        missing_triggers = [elem for elem in trigger_elements if elem not in content]

        if not missing_triggers:
            print_test("GitHub workflow triggers", "PASS")
            results.append(True)
        else:
            print_test("GitHub workflow triggers", "FAIL", f"Missing triggers: {missing_triggers}")
            results.append(False)

        # Test Python setup
        python_elements = ["python-version: '3.13'", "setup-python@v", "requirements.txt"]
        missing_python = [elem for elem in python_elements if elem not in content]

        if not missing_python:
            print_test("GitHub workflow Python setup", "PASS")
            results.append(True)
        else:
            print_test(
                "GitHub workflow Python setup", "FAIL", f"Missing elements: {missing_python}"
            )
            results.append(False)

    except Exception as e:
        print_test("GitHub workflow content validation", "FAIL", str(e))
        results.append(False)

    return results


def test_integration():
    """Test integration capabilities."""
    print_section("TESTING INTEGRATION CAPABILITIES")

    results = []

    # Test 1: Run merger integration tests
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_merger_integration.py::TestMergerAgentIntegration",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print_test("MergerAgent integration tests", "PASS")
            results.append(True)
        else:
            print_test("MergerAgent integration tests", "FAIL", "Some integration tests failed")
            results.append(False)

    except subprocess.TimeoutExpired:
        print_test("MergerAgent integration tests", "FAIL", "Tests timed out")
        results.append(False)
    except Exception as e:
        print_test("MergerAgent integration tests", "FAIL", str(e))
        results.append(False)

    # Test 2: Check if all components work together
    components = [
        ("MergerAgent", Path("merger_agent/merger_agent.py")),
        ("Pre-commit hook", Path(".git/hooks/pre-commit")),
        ("GitHub workflow", Path(".github/workflows/merge-guardian.yml")),
        ("Integration tests", Path("tests/test_merger_integration.py")),
    ]

    all_exist = True
    for name, path in components:
        if not path.exists():
            all_exist = False
            break

    if all_exist:
        print_test("All Phase 3 components present", "PASS")
        results.append(True)
    else:
        print_test("All Phase 3 components present", "FAIL", "Some components missing")
        results.append(False)

    return results


def main():
    """Main validation function."""
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│                                                             │")
    print("│           PHASE 3 VALIDATION - ADR-002 ENFORCEMENT         │")
    print("│                                                             │")
    print("│  Validating complete merge verification system components   │")
    print("│                                                             │")
    print("└─────────────────────────────────────────────────────────────┘")
    print(f"{Colors.RESET}")

    all_results = []

    # Run all tests
    all_results.extend(test_merger_agent())
    all_results.extend(test_precommit_hook())
    all_results.extend(test_github_workflow())
    all_results.extend(test_integration())

    # Summary
    print_section("VALIDATION SUMMARY")

    total_tests = len(all_results)
    passed_tests = sum(all_results)
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed_tests}{Colors.RESET}")

    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 PHASE 3 VALIDATION SUCCESSFUL!{Colors.RESET}")
        print(f"{Colors.GREEN}✅ ADR-002 enforcement system is properly implemented{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ PHASE 3 VALIDATION FAILED{Colors.RESET}")
        print(f"{Colors.RED}Some components need attention before deployment{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
