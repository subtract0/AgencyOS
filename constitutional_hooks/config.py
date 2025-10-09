"""
Configuration for constitutional enforcement rules.

These rules map directly to the 5 Constitutional Articles in constitution.md.
"""

# Article I: Complete Context Before Action
# Patterns that indicate attempts to skip context or work with incomplete information
PROMPT_DENY_LIST_PATTERNS = [
    r"skip\s+tests?",  # "skip test", "skip tests"
    r"skip\s+.*\s+tests?",  # "skip integration tests"
    r"Dict\[Any,\s*Any\]",  # Violates strict typing (Article I context requirement)
    r"Dict\[str,\s*Any\]",  # Also violates strict typing
    r"type:\s*ignore",  # Bypasses type checking
    r"--no-verify",  # Git commit without verification
    r"bypass",  # General bypass attempts
    r"force\s+push",  # Force push (risky, requires verification)
    r"assume\s+",  # "assume this works", "assume tests pass"
    r"without\s+test",  # "commit without test", "merge without test"
]

# Article II: 100% Verification and Stability
ARTICLE_II_MIN_PASS_PERCENTAGE = 1.0  # 100% - no exceptions
ARTICLE_II_ALLOW_SKIPPED = False  # Skipped tests count as incomplete context

# Article III: Automated Merge Enforcement
GIT_COMMANDS_TO_ENFORCE = [
    "git_commit",
    "git_push",
    "bash_git_commit",
    "bash_git_push",
]

# Article IV: Continuous Learning (not enforced by hooks, but listed for reference)
# VectorStore integration is mandatory per constitution

# Article V: Spec-Driven Development
# Definition of Done threshold for session completion
DEFINITION_OF_DONE_THRESHOLD = 0.95  # 95% of tasks must be completed

# Hook exit codes
EXIT_SUCCESS = 0  # Allow action to proceed
EXIT_BLOCK = 2  # Block action (constitutional violation)
EXIT_ERROR = 1  # Script error (unexpected failure)
