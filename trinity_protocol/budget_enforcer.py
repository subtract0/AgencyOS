"""
Budget Enforcer for Trinity Protocol

Hard budget limits for autonomous operation.

Constitutional Compliance:
- Article III: Automated enforcement (no manual overrides)

Safety Features:
- Hard daily limit ($30/day for autonomous)
- Real-time tracking via CostTracker
- Alert at 80% threshold
- Auto-shutdown at limit
- No bypass capability
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, List
from trinity_protocol.cost_tracker import CostTracker


class BudgetStatus(Enum):
    """Budget health status."""

    HEALTHY = "healthy"    # Within budget and threshold
    WARNING = "warning"    # Threshold reached, approaching limit
    EXCEEDED = "exceeded"  # Budget limit exceeded, operations blocked


class BudgetExceededError(Exception):
    """
    Raised when budget limit exceeded.

    This is a BLOCKER - autonomous operation must stop.
    """
    pass


@dataclass
class BudgetAlert:
    """Budget alert notification."""

    alert_type: str  # threshold_reached, limit_approaching
    current_spending_usd: float
    daily_limit_usd: float
    remaining_usd: float
    threshold_percent: int
    timestamp: str
    message: str


@dataclass
class BudgetStatusReport:
    """Current budget status."""

    status: BudgetStatus
    current_spending_usd: float
    daily_limit_usd: float
    remaining_usd: float
    percent_used: float
    alert_threshold_usd: float
    timestamp: str


class BudgetEnforcer:
    """
    Enforces hard budget limits for autonomous operation.

    Safety Features:
    - Hard daily limit (default: $30/day)
    - Real-time cost tracking
    - Alert at configurable threshold (default: 80%)
    - Automatic shutdown at limit
    - NO manual override capability (Article III)

    Usage:
        enforcer = BudgetEnforcer(
            cost_tracker=cost_tracker,
            daily_limit_usd=30.0,
            shutdown_callback=executor.stop
        )

        # Before each operation
        enforcer.enforce()  # Raises BudgetExceededError if over limit

        # Check for alerts
        alerts = enforcer.check_alerts()
        for alert in alerts:
            print(alert.message)
    """

    def __init__(
        self,
        cost_tracker: CostTracker,
        daily_limit_usd: float = 30.0,
        alert_threshold: float = 0.8,  # 80%
        shutdown_callback: Optional[Callable[[], None]] = None
    ):
        """
        Initialize budget enforcer.

        Args:
            cost_tracker: CostTracker instance for real-time cost monitoring
            daily_limit_usd: Daily spending limit in USD
            alert_threshold: Threshold for warning alerts (0.0-1.0)
            shutdown_callback: Optional callback to invoke on budget exceeded
        """
        self.cost_tracker = cost_tracker
        self.daily_limit_usd = daily_limit_usd
        self.alert_threshold = alert_threshold
        self.shutdown_callback = shutdown_callback
        self._alert_triggered = False  # Track if alert already sent

    def get_status(self) -> BudgetStatusReport:
        """
        Get current budget status.

        Returns:
            BudgetStatusReport with current state
        """
        # Get today's spending
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        summary = self.cost_tracker.get_summary(since=today_start)

        current_spending = summary.total_cost_usd
        remaining = self.daily_limit_usd - current_spending
        percent_used = (current_spending / self.daily_limit_usd) * 100
        alert_threshold_usd = self.daily_limit_usd * self.alert_threshold

        # Determine status
        if current_spending >= self.daily_limit_usd:
            status = BudgetStatus.EXCEEDED
        elif current_spending >= alert_threshold_usd:
            status = BudgetStatus.WARNING
        else:
            status = BudgetStatus.HEALTHY

        return BudgetStatusReport(
            status=status,
            current_spending_usd=current_spending,
            daily_limit_usd=self.daily_limit_usd,
            remaining_usd=remaining,
            percent_used=percent_used,
            alert_threshold_usd=alert_threshold_usd,
            timestamp=datetime.now().isoformat()
        )

    def enforce(self) -> None:
        """
        Enforce budget limit.

        Raises:
            BudgetExceededError: If daily budget exceeded
        """
        status = self.get_status()

        if status.status == BudgetStatus.EXCEEDED:
            # Invoke shutdown callback if provided
            if self.shutdown_callback:
                self.shutdown_callback()

            # Raise blocking exception
            error_msg = self._format_budget_exceeded_error(status)
            raise BudgetExceededError(error_msg)

    def check_alerts(self) -> List[BudgetAlert]:
        """
        Check for budget alerts.

        Returns:
            List of active budget alerts
        """
        status = self.get_status()
        alerts = []

        # Alert at threshold (only once)
        if status.status == BudgetStatus.WARNING and not self._alert_triggered:
            threshold_percent = int(self.alert_threshold * 100)
            alert = BudgetAlert(
                alert_type="threshold_reached",
                current_spending_usd=status.current_spending_usd,
                daily_limit_usd=status.daily_limit_usd,
                remaining_usd=status.remaining_usd,
                threshold_percent=threshold_percent,
                timestamp=datetime.now().isoformat(),
                message=self._format_threshold_alert(status, threshold_percent)
            )
            alerts.append(alert)
            self._alert_triggered = True

        return alerts

    def _format_budget_exceeded_error(self, status: BudgetStatusReport) -> str:
        """
        Format budget exceeded error message.

        Args:
            status: Current budget status

        Returns:
            Formatted error message
        """
        msg_parts = [
            "BUDGET EXCEEDED - AUTONOMOUS OPERATION BLOCKED",
            "",
            f"Daily Limit: ${status.daily_limit_usd:.2f}",
            f"Current Spending: ${status.current_spending_usd:.2f}",
            f"Overage: ${status.current_spending_usd - status.daily_limit_usd:.2f}",
            "",
            "Constitutional Compliance: Article III - Automated Enforcement",
            "Budget limits are ABSOLUTE. No manual override permitted.",
            "",
            "REQUIRED ACTION:",
            "1. Review cost dashboard for spending breakdown",
            "2. Wait for daily reset (midnight UTC)",
            "3. Consider increasing daily limit if justified",
            "4. Autonomous operation will AUTO-SHUTDOWN",
            "",
            "System will now halt all autonomous operations."
        ]

        return "\n".join(msg_parts)

    def _format_threshold_alert(self, status: BudgetStatusReport, threshold_percent: int) -> str:
        """
        Format threshold alert message.

        Args:
            status: Current budget status
            threshold_percent: Alert threshold percentage

        Returns:
            Formatted alert message
        """
        return (
            f"⚠️  BUDGET ALERT: {threshold_percent}% threshold reached\n"
            f"Current: ${status.current_spending_usd:.2f} / ${status.daily_limit_usd:.2f}\n"
            f"Remaining: ${status.remaining_usd:.2f}\n"
            f"Operations will be blocked at ${status.daily_limit_usd:.2f}"
        )
