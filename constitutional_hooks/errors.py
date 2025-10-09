"""
Custom error types for constitutional enforcement.
"""


class ConstitutionalError(Exception):
    """Constitutional violation detected."""

    def __init__(self, message: str, rule_id: str):
        """
        Initialize constitutional error.

        Args:
            message: Human-readable error message
            rule_id: Constitutional article ID (e.g., "Article I", "Article II")
        """
        self.message = message
        self.rule_id = rule_id
        super().__init__(f"{rule_id}: {message}")
