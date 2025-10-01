#!/usr/bin/env python3
"""
Cost Alert System for Trinity Protocol.

Monitors spending patterns and sends notifications when:
- Budget thresholds exceeded (80%, 90%, 100%)
- Hourly spending rate anomalies
- Daily budget on track to exceed
- Sudden cost spikes detected

Supports multiple notification channels:
- Console/Log alerts (always enabled)
- Email notifications (optional)
- Slack webhooks (optional)
- Custom webhook callbacks (extensible)

Usage:
    from trinity_protocol.cost_alerts import CostAlertSystem, AlertConfig

    # Basic setup
    config = AlertConfig(
        budget_threshold_pct=[80, 90, 100],
        hourly_rate_max=1.0,
        daily_budget_max=10.0
    )

    alerts = CostAlertSystem(cost_tracker, config)
    alerts.check_all()  # Run all checks
"""

import logging
import smtplib
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Callable, Dict, List, Optional
from enum import Enum

# Try to import optional dependencies
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.cost_tracker import CostTracker


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert notification."""

    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    cost: Optional[float] = None
    threshold: Optional[float] = None


@dataclass
class AlertConfig:
    """Configuration for cost alert system."""

    # Budget alerts
    budget_threshold_pct: List[float] = field(default_factory=lambda: [80, 90, 100])

    # Rate alerts
    hourly_rate_max: Optional[float] = None  # USD per hour
    daily_budget_max: Optional[float] = None  # USD per day

    # Spike detection
    spike_multiplier: float = 3.0  # Alert if current rate is 3x baseline
    spike_window_hours: int = 1  # Compare last hour to baseline

    # Email configuration (optional)
    email_enabled: bool = False
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_from: Optional[str] = None
    email_to: Optional[List[str]] = None
    email_password: Optional[str] = None

    # Slack configuration (optional)
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None

    # Alert deduplication (don't spam same alert)
    alert_cooldown_minutes: int = 60

    # Logging
    log_to_file: bool = True
    log_file_path: str = "trinity_alerts.log"


class CostAlertSystem:
    """
    Monitors costs and sends alerts based on configured thresholds.

    Features:
    - Budget threshold alerts
    - Hourly rate monitoring
    - Daily projection alerts
    - Anomaly detection
    - Multi-channel notifications
    """

    def __init__(
        self,
        cost_tracker: CostTracker,
        config: Optional[AlertConfig] = None
    ):
        """
        Initialize alert system.

        Args:
            cost_tracker: CostTracker instance to monitor
            config: Alert configuration (uses defaults if not provided)
        """
        self.tracker = cost_tracker
        self.config = config or AlertConfig()

        # Track fired alerts to prevent spam
        self._fired_alerts: Dict[str, datetime] = {}

        # Setup logging
        self._setup_logging()

        self.logger.info("Cost alert system initialized")

    def _setup_logging(self) -> None:
        """Setup logging for alerts."""
        self.logger = logging.getLogger("trinity.cost_alerts")
        self.logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (optional)
        if self.config.log_to_file:
            file_handler = logging.FileHandler(self.config.log_file_path)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(console_formatter)
            self.logger.addHandler(file_handler)

    def check_all(self) -> List[Alert]:
        """
        Run all alert checks.

        Returns:
            List of triggered alerts
        """
        alerts: List[Alert] = []

        # Budget threshold checks
        alerts.extend(self.check_budget_thresholds())

        # Rate checks
        if self.config.hourly_rate_max:
            alert = self.check_hourly_rate()
            if alert:
                alerts.append(alert)

        if self.config.daily_budget_max:
            alert = self.check_daily_projection()
            if alert:
                alerts.append(alert)

        # Spike detection
        alert = self.check_spending_spike()
        if alert:
            alerts.append(alert)

        # Send notifications for all triggered alerts
        for alert in alerts:
            self._send_alert(alert)

        return alerts

    def check_budget_thresholds(self) -> List[Alert]:
        """
        Check if budget thresholds exceeded.

        Returns:
            List of threshold alerts
        """
        if not self.tracker.budget_usd:
            return []

        summary = self.tracker.get_summary()
        spent = summary.total_cost_usd
        budget = self.tracker.budget_usd
        percent = (spent / budget) * 100

        alerts = []

        for threshold in self.config.budget_threshold_pct:
            if percent >= threshold:
                # Check if we've already alerted for this threshold recently
                alert_key = f"budget_{threshold}"
                if self._is_alert_on_cooldown(alert_key):
                    continue

                # Determine severity
                if threshold >= 100:
                    level = AlertLevel.CRITICAL
                elif threshold >= 90:
                    level = AlertLevel.WARNING
                else:
                    level = AlertLevel.INFO

                alert = Alert(
                    level=level,
                    title=f"Budget {threshold}% Threshold Exceeded",
                    message=(
                        f"Spent ${spent:.4f} of ${budget:.2f} budget "
                        f"({percent:.1f}%). Threshold: {threshold}%"
                    ),
                    cost=spent,
                    threshold=threshold
                )

                alerts.append(alert)
                self._record_alert(alert_key)

        return alerts

    def check_hourly_rate(self) -> Optional[Alert]:
        """
        Check if hourly spending rate exceeds limit.

        Returns:
            Alert if rate exceeded, None otherwise
        """
        one_hour_ago = datetime.now() - timedelta(hours=1)
        hourly_summary = self.tracker.get_summary(since=one_hour_ago)
        hourly_cost = hourly_summary.total_cost_usd

        if hourly_cost > self.config.hourly_rate_max:
            alert_key = "hourly_rate"
            if self._is_alert_on_cooldown(alert_key):
                return None

            alert = Alert(
                level=AlertLevel.WARNING,
                title="Hourly Spending Rate Exceeded",
                message=(
                    f"Spent ${hourly_cost:.4f} in the last hour. "
                    f"Limit: ${self.config.hourly_rate_max:.2f}/hour"
                ),
                cost=hourly_cost,
                threshold=self.config.hourly_rate_max
            )

            self._record_alert(alert_key)
            return alert

        return None

    def check_daily_projection(self) -> Optional[Alert]:
        """
        Check if daily spending projection exceeds budget.

        Returns:
            Alert if projection exceeded, None otherwise
        """
        # Calculate current hourly rate
        one_hour_ago = datetime.now() - timedelta(hours=1)
        hourly_summary = self.tracker.get_summary(since=one_hour_ago)
        hourly_rate = hourly_summary.total_cost_usd

        # Project to 24 hours
        daily_projection = hourly_rate * 24

        if daily_projection > self.config.daily_budget_max:
            alert_key = "daily_projection"
            if self._is_alert_on_cooldown(alert_key):
                return None

            alert = Alert(
                level=AlertLevel.WARNING,
                title="Daily Budget Projection Exceeded",
                message=(
                    f"Current spending rate projects to ${daily_projection:.2f}/day. "
                    f"Daily limit: ${self.config.daily_budget_max:.2f}"
                ),
                cost=daily_projection,
                threshold=self.config.daily_budget_max
            )

            self._record_alert(alert_key)
            return alert

        return None

    def check_spending_spike(self) -> Optional[Alert]:
        """
        Detect anomalous spending spikes.

        Returns:
            Alert if spike detected, None otherwise
        """
        # Get baseline (average hourly rate over last 24 hours)
        one_day_ago = datetime.now() - timedelta(days=1)
        daily_summary = self.tracker.get_summary(since=one_day_ago)

        # Need at least 24 hours of data
        if daily_summary.total_calls < 10:
            return None

        baseline_hourly = daily_summary.total_cost_usd / 24

        # Get current rate (last hour)
        window_start = datetime.now() - timedelta(hours=self.config.spike_window_hours)
        window_summary = self.tracker.get_summary(since=window_start)
        current_hourly = window_summary.total_cost_usd / self.config.spike_window_hours

        # Check for spike
        if baseline_hourly > 0 and current_hourly > baseline_hourly * self.config.spike_multiplier:
            alert_key = "spending_spike"
            if self._is_alert_on_cooldown(alert_key):
                return None

            multiplier = current_hourly / baseline_hourly

            alert = Alert(
                level=AlertLevel.WARNING,
                title="Spending Spike Detected",
                message=(
                    f"Current spending rate (${current_hourly:.4f}/hour) is "
                    f"{multiplier:.1f}x baseline (${baseline_hourly:.4f}/hour)"
                ),
                cost=current_hourly,
                threshold=baseline_hourly
            )

            self._record_alert(alert_key)
            return alert

        return None

    def _is_alert_on_cooldown(self, alert_key: str) -> bool:
        """Check if alert is in cooldown period."""
        if alert_key not in self._fired_alerts:
            return False

        last_fired = self._fired_alerts[alert_key]
        cooldown = timedelta(minutes=self.config.alert_cooldown_minutes)

        return datetime.now() - last_fired < cooldown

    def _record_alert(self, alert_key: str) -> None:
        """Record that an alert was fired."""
        self._fired_alerts[alert_key] = datetime.now()

    def _send_alert(self, alert: Alert) -> None:
        """
        Send alert through all enabled channels.

        Args:
            alert: Alert to send
        """
        # Always log
        log_msg = f"[{alert.level.value.upper()}] {alert.title}: {alert.message}"

        if alert.level == AlertLevel.CRITICAL:
            self.logger.critical(log_msg)
        elif alert.level == AlertLevel.WARNING:
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)

        # Send to email if configured
        if self.config.email_enabled:
            self._send_email_alert(alert)

        # Send to Slack if configured
        if self.config.slack_enabled:
            self._send_slack_alert(alert)

    def _send_email_alert(self, alert: Alert) -> None:
        """Send alert via email."""
        if not all([
            self.config.email_smtp_host,
            self.config.email_from,
            self.config.email_to,
            self.config.email_password
        ]):
            self.logger.warning("Email alerts enabled but configuration incomplete")
            return

        try:
            # Create message
            msg = MIMEText(alert.message)
            msg['Subject'] = f"[Trinity Alert] {alert.title}"
            msg['From'] = self.config.email_from
            msg['To'] = ", ".join(self.config.email_to)

            # Send via SMTP
            with smtplib.SMTP(self.config.email_smtp_host, self.config.email_smtp_port) as server:
                server.starttls()
                server.login(self.config.email_from, self.config.email_password)
                server.send_message(msg)

            self.logger.info(f"Email alert sent: {alert.title}")

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")

    def _send_slack_alert(self, alert: Alert) -> None:
        """Send alert to Slack webhook."""
        if not HAS_REQUESTS:
            self.logger.warning("Slack alerts require 'requests' library")
            return

        if not self.config.slack_webhook_url:
            self.logger.warning("Slack alerts enabled but webhook URL not configured")
            return

        # Choose emoji based on severity
        emoji_map = {
            AlertLevel.INFO: ":information_source:",
            AlertLevel.WARNING: ":warning:",
            AlertLevel.CRITICAL: ":rotating_light:"
        }
        emoji = emoji_map.get(alert.level, ":bell:")

        # Format message
        payload = {
            "text": f"{emoji} *{alert.title}*",
            "attachments": [
                {
                    "color": "danger" if alert.level == AlertLevel.CRITICAL else "warning",
                    "fields": [
                        {
                            "title": "Message",
                            "value": alert.message,
                            "short": False
                        },
                        {
                            "title": "Timestamp",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "short": True
                        },
                        {
                            "title": "Level",
                            "value": alert.level.value.upper(),
                            "short": True
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            self.logger.info(f"Slack alert sent: {alert.title}")

        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")

    def get_alert_summary(self) -> Dict[str, int]:
        """
        Get summary of fired alerts.

        Returns:
            Dictionary of alert counts by key
        """
        summary = {}
        for alert_key, timestamp in self._fired_alerts.items():
            summary[alert_key] = summary.get(alert_key, 0) + 1
        return summary


def run_continuous_monitoring(
    cost_tracker: CostTracker,
    config: AlertConfig,
    check_interval_seconds: int = 300
) -> None:
    """
    Run continuous cost monitoring with periodic checks.

    Args:
        cost_tracker: CostTracker to monitor
        config: Alert configuration
        check_interval_seconds: Seconds between checks (default: 5 minutes)
    """
    import time

    alert_system = CostAlertSystem(cost_tracker, config)

    print(f"Starting continuous cost monitoring (checking every {check_interval_seconds}s)")
    print("Press Ctrl+C to stop")

    try:
        while True:
            alerts = alert_system.check_all()

            if alerts:
                print(f"\n⚠️  {len(alerts)} alert(s) triggered at {datetime.now()}")
                for alert in alerts:
                    print(f"  [{alert.level.value}] {alert.title}")

            time.sleep(check_interval_seconds)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        summary = alert_system.get_alert_summary()
        if summary:
            print("\nAlert Summary:")
            for alert_key, count in summary.items():
                print(f"  {alert_key}: {count} time(s)")


def main():
    """Main entry point for cost alert CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Trinity Protocol Cost Alert System"
    )

    parser.add_argument(
        "--db",
        type=str,
        default="trinity_costs.db",
        help="Path to cost database"
    )

    parser.add_argument(
        "--budget",
        type=float,
        help="Budget limit in USD"
    )

    parser.add_argument(
        "--hourly-max",
        type=float,
        help="Maximum hourly spending rate (USD/hour)"
    )

    parser.add_argument(
        "--daily-max",
        type=float,
        help="Maximum daily spending (USD/day)"
    )

    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuous monitoring"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval for continuous mode (seconds, default: 300)"
    )

    args = parser.parse_args()

    # Initialize tracker
    tracker = CostTracker(db_path=args.db, budget_usd=args.budget)

    # Build config
    config = AlertConfig(
        hourly_rate_max=args.hourly_max,
        daily_budget_max=args.daily_max
    )

    if args.continuous:
        run_continuous_monitoring(tracker, config, args.interval)
    else:
        # Single check
        alert_system = CostAlertSystem(tracker, config)
        alerts = alert_system.check_all()

        if alerts:
            print(f"\n⚠️  {len(alerts)} alert(s) triggered:")
            for alert in alerts:
                print(f"\n[{alert.level.value.upper()}] {alert.title}")
                print(f"  {alert.message}")
        else:
            print("✅ No alerts triggered. All costs within limits.")


if __name__ == "__main__":
    main()
