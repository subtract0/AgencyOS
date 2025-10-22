"""Example usage of CompletionValidator for STEP 6.5 validation gate.

This example demonstrates how to use the autonomous completion validator
to enforce 100% task completion before generating execution reports.

Constitutional Compliance:
- Article I: Complete context validation
- Article II: 100% verification requirement
- Article III: Automated enforcement
- Article IV: VectorStore pattern storage
- Article V: Spec-driven validation

Usage:
    python tools/orchestrator/completion_validator_example.py
"""

from tools.orchestrator.completion_validator import CompletionValidator


def example_successful_validation():
    """Example: Successful validation with all checks passing."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Successful Validation")
    print("=" * 70 + "\n")

    # Simulate completed primeA execution
    validator = CompletionValidator(
        task_results=[
            {
                "id": "spec_generation",
                "status": "success",
                "acceptance_criteria_met": True,
                "type": "spec",
            },
            {
                "id": "test_writing",
                "status": "success",
                "acceptance_criteria_met": True,
                "type": "test",
            },
            {
                "id": "implementation",
                "status": "success",
                "acceptance_criteria_met": True,
                "type": "code",
            },
            {
                "id": "test_verification",
                "status": "success",
                "acceptance_criteria_met": True,
                "type": "test",
            },
        ],
        todos=[
            {
                "content": "Phase 1: Spec Generation",
                "status": "completed",
                "activeForm": "Completed",
            },
            {
                "content": "Phase 2: Test Writing",
                "status": "completed",
                "activeForm": "Completed",
            },
            {
                "content": "Phase 3: Implementation",
                "status": "completed",
                "activeForm": "Completed",
            },
            {
                "content": "Phase 4: Verification",
                "status": "completed",
                "activeForm": "Completed",
            },
            {
                "content": "Post-execution reflection",
                "status": "completed",
                "activeForm": "Completed",
            },
        ],
        spec_criteria=[
            "Feature A: Authentication implemented",
            "Feature B: Error handling tested",
            "Feature C: Documentation complete",
        ],
        backlog_items=[],
        context_usage=0.85,
    )

    result = validator.validate()

    if result.is_ok():
        validation = result.unwrap()
        print(validation.get_summary())
        print("\n✅ PROCEED TO STEP 7: Generate Execution Report")
    else:
        error = result.unwrap_err()
        print(f"❌ VALIDATION FAILED: {error.message}")


def example_incomplete_tasks():
    """Example: Validation fails due to incomplete tasks."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Incomplete Tasks (Validation Failure)")
    print("=" * 70 + "\n")

    validator = CompletionValidator(
        task_results=[
            {
                "id": "task1",
                "status": "success",
                "acceptance_criteria_met": True,
                "type": "code",
            },
            {
                "id": "task2",
                "status": "pending",
                "acceptance_criteria_met": False,
                "type": "code",
            },
        ],
        todos=[
            {"content": "Task 1", "status": "completed", "activeForm": "Completed"},
            {"content": "Task 2", "status": "in_progress", "activeForm": "Working"},
        ],
        spec_criteria=["Feature implemented"],
        backlog_items=[],
    )

    result = validator.validate()

    if result.is_err():
        error = result.unwrap_err()
        print(f"❌ VALIDATION FAILED: {error.reason}")
        print(f"\n{error.message}\n")
        print("Failed Checks:")
        for check in error.failed_checks:
            print(f"  ❌ {check}")
        print("\nSuggestions:")
        for suggestion in error.suggestions:
            print(f"  💡 {suggestion}")
        print("\n⚠️ EXECUTION CONTINUES UNTIL VALIDATION PASSES")
    else:
        print("Unexpected success")


def example_backlog_warning():
    """Example: Validation succeeds with backlog warning."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Backlog Warning (Non-blocking)")
    print("=" * 70 + "\n")

    validator = CompletionValidator(
        task_results=[
            {
                "id": "task1",
                "status": "success",
                "acceptance_criteria_met": True,
                "type": "code",
            }
        ],
        todos=[{"content": "Task 1", "status": "completed", "activeForm": "Completed"}],
        spec_criteria=["Feature implemented"],
        backlog_items=[
            "TODO: Optimize performance (low priority)",
            "TODO: Add additional error cases",
        ],
        context_usage=0.75,
    )

    result = validator.validate()

    if result.is_ok():
        validation = result.unwrap()
        print(validation.get_summary())
        print("\n✅ VALIDATION PASSED (with warnings)")
        print("Note: Backlog items present but non-blocking")
    else:
        error = result.unwrap_err()
        print(f"Unexpected failure: {error.message}")


def example_constitutional_checks():
    """Example: Detailed constitutional compliance checks."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Constitutional Compliance Checks")
    print("=" * 70 + "\n")

    validator = CompletionValidator(
        task_results=[
            {
                "id": "task1",
                "status": "success",
                "acceptance_criteria_met": True,
                "type": "code",
            }
        ],
        todos=[{"content": "Task 1", "status": "completed", "activeForm": "Completed"}],
        spec_criteria=["Feature implemented"],
        backlog_items=[],
        context_usage=0.92,
    )

    result = validator.validate()

    if result.is_ok():
        validation = result.unwrap()
        print("Constitutional Compliance Report:\n")

        checks = validation.constitutional_checks
        print(f"Article I (Complete Context): {'✅' if checks.article_i else '❌'}")
        print(f"  {checks.details['Article I']}")
        print(f"\nArticle II (100% Verification): {'✅' if checks.article_ii else '❌'}")
        print(f"  {checks.details['Article II']}")
        print(f"\nArticle III (Automated Enforcement): {'✅' if checks.article_iii else '❌'}")
        print(f"  {checks.details['Article III']}")
        print(f"\nArticle IV (Continuous Learning): {'✅' if checks.article_iv else '❌'}")
        print(f"  {checks.details['Article IV']}")
        print(f"\nArticle V (Spec-Driven Development): {'✅' if checks.article_v else '❌'}")
        print(f"  {checks.details['Article V']}")

        print(f"\nContext Efficiency: {validation.context_efficiency:.1%}")
        print(f"Overall Compliance: {'✅ PASS' if validation.is_complete() else '❌ FAIL'}")
    else:
        error = result.unwrap_err()
        print(f"Validation failed: {error.message}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COMPLETION VALIDATOR EXAMPLES")
    print("Article I-V Constitutional Enforcement")
    print("=" * 70)

    example_successful_validation()
    example_incomplete_tasks()
    example_backlog_warning()
    example_constitutional_checks()

    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70 + "\n")
