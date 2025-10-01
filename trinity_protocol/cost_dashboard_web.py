#!/usr/bin/env python3
"""
Web-based real-time cost dashboard for Trinity Protocol.

Features:
- Real-time updates via Server-Sent Events (SSE)
- Interactive charts with Chart.js
- Mobile-friendly responsive design
- REST API for cost data
- Budget visualization
- Agent breakdown charts

Usage:
    # Start web server
    python trinity_protocol/cost_dashboard_web.py --port 8080

    # Then open http://localhost:8080 in browser

Dependencies:
    pip install flask
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Generator

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.cost_tracker import CostTracker

# Try to import Flask
try:
    from flask import Flask, render_template_string, jsonify, Response, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("ERROR: Flask not installed. Install with: pip install flask")
    sys.exit(1)


# HTML template with embedded CSS and JavaScript
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trinity Protocol - Cost Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            margin-bottom: 30px;
        }

        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header .subtitle {
            color: #666;
            font-size: 1.1em;
        }

        .header .status {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-left: 15px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }

        .card h2 {
            color: #667eea;
            font-size: 1.3em;
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            color: #666;
            font-size: 0.95em;
        }

        .metric-value {
            font-size: 1.4em;
            font-weight: 600;
            color: #333;
        }

        .metric-value.success {
            color: #10b981;
        }

        .metric-value.warning {
            color: #f59e0b;
        }

        .metric-value.danger {
            color: #ef4444;
        }

        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }

        .budget-bar {
            width: 100%;
            height: 30px;
            background: #e5e7eb;
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
            position: relative;
        }

        .budget-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981, #059669);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9em;
        }

        .budget-bar-fill.warning {
            background: linear-gradient(90deg, #f59e0b, #d97706);
        }

        .budget-bar-fill.danger {
            background: linear-gradient(90deg, #ef4444, #dc2626);
        }

        .agent-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .agent-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }

        .agent-name {
            font-weight: 500;
            color: #333;
        }

        .agent-cost {
            font-weight: 600;
            color: #667eea;
        }

        .agent-bar {
            width: 100%;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            margin-top: 5px;
            overflow: hidden;
        }

        .agent-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }

        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 0.9em;
        }

        .timestamp {
            color: white;
            text-align: center;
            margin-top: 15px;
            font-size: 0.95em;
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Trinity Protocol Cost Dashboard <span class="status" id="status">● LIVE</span></h1>
            <p class="subtitle">Real-time LLM cost monitoring and budget tracking</p>
        </div>

        <div class="grid">
            <div class="card">
                <h2>💰 Total Spending</h2>
                <div class="metric">
                    <span class="metric-label">Total Cost</span>
                    <span class="metric-value" id="total-cost">$0.0000</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Calls</span>
                    <span class="metric-value" id="total-calls">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Tokens</span>
                    <span class="metric-value" id="total-tokens">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Success Rate</span>
                    <span class="metric-value success" id="success-rate">100%</span>
                </div>
            </div>

            <div class="card">
                <h2>📈 Spending Trends</h2>
                <div class="metric">
                    <span class="metric-label">Hourly Rate</span>
                    <span class="metric-value" id="hourly-rate">$0.0000/hr</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Daily Projection</span>
                    <span class="metric-value" id="daily-projection">$0.00/day</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Hour</span>
                    <span class="metric-value" id="last-hour">$0.0000</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last 24h</span>
                    <span class="metric-value" id="last-day">$0.0000</span>
                </div>
            </div>

            <div class="card" id="budget-card" style="display: none;">
                <h2>📊 Budget Status</h2>
                <div class="metric">
                    <span class="metric-label">Budget</span>
                    <span class="metric-value" id="budget-limit">$0.00</span>
                </div>
                <div class="budget-bar">
                    <div class="budget-bar-fill" id="budget-fill" style="width: 0%">
                        <span id="budget-percent">0%</span>
                    </div>
                </div>
                <div class="metric">
                    <span class="metric-label">Remaining</span>
                    <span class="metric-value success" id="budget-remaining">$0.00</span>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>🤖 Cost by Agent</h2>
                <div class="agent-list" id="agent-list">
                    <p style="color: #999; text-align: center;">No data available</p>
                </div>
            </div>

            <div class="card">
                <h2>📊 Cost Distribution</h2>
                <div class="chart-container">
                    <canvas id="agent-chart"></canvas>
                </div>
            </div>
        </div>

        <p class="timestamp">Last updated: <span id="last-update">--</span></p>
        <div class="footer">
            Trinity Protocol • Real-time Cost Monitoring
        </div>
    </div>

    <script>
        // Initialize Chart.js
        const ctx = document.getElementById('agent-chart').getContext('2d');
        let agentChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#667eea', '#764ba2', '#f59e0b', '#10b981',
                        '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // Connect to SSE stream for live updates
        const eventSource = new EventSource('/stream');

        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };

        eventSource.onerror = function(error) {
            document.getElementById('status').textContent = '● DISCONNECTED';
            document.getElementById('status').style.background = '#ef4444';
        };

        function updateDashboard(data) {
            const summary = data.summary;
            const trends = data.trends;

            // Update totals
            document.getElementById('total-cost').textContent = `$${summary.total_cost_usd.toFixed(4)}`;
            document.getElementById('total-calls').textContent = summary.total_calls.toLocaleString();
            document.getElementById('total-tokens').textContent =
                (summary.total_input_tokens + summary.total_output_tokens).toLocaleString();

            const successRate = document.getElementById('success-rate');
            const rate = (summary.success_rate * 100).toFixed(1);
            successRate.textContent = `${rate}%`;
            successRate.className = 'metric-value ' + (rate >= 95 ? 'success' : rate >= 80 ? 'warning' : 'danger');

            // Update trends
            document.getElementById('hourly-rate').textContent = `$${trends.hourly_rate.toFixed(4)}/hr`;
            document.getElementById('daily-projection').textContent = `$${trends.daily_projection.toFixed(2)}/day`;
            document.getElementById('last-hour').textContent = `$${trends.last_hour_cost.toFixed(4)}`;
            document.getElementById('last-day').textContent = `$${trends.last_day_cost.toFixed(4)}`;

            // Update budget (if exists)
            if (data.budget && data.budget.limit) {
                document.getElementById('budget-card').style.display = 'block';
                document.getElementById('budget-limit').textContent = `$${data.budget.limit.toFixed(2)}`;
                document.getElementById('budget-remaining').textContent = `$${data.budget.remaining.toFixed(4)}`;

                const percent = data.budget.percent_used;
                const budgetFill = document.getElementById('budget-fill');
                budgetFill.style.width = `${Math.min(percent, 100)}%`;
                document.getElementById('budget-percent').textContent = `${percent.toFixed(1)}%`;

                budgetFill.className = 'budget-bar-fill';
                if (percent >= 100) {
                    budgetFill.className += ' danger';
                } else if (percent >= 80) {
                    budgetFill.className += ' warning';
                }
            }

            // Update agent list
            if (summary.by_agent && Object.keys(summary.by_agent).length > 0) {
                const agentList = document.getElementById('agent-list');
                const maxCost = Math.max(...Object.values(summary.by_agent));

                agentList.innerHTML = '';
                const sortedAgents = Object.entries(summary.by_agent)
                    .sort((a, b) => b[1] - a[1]);

                sortedAgents.forEach(([agent, cost]) => {
                    const item = document.createElement('div');
                    item.className = 'agent-item';

                    const percent = ((cost / summary.total_cost_usd) * 100).toFixed(1);
                    const barWidth = ((cost / maxCost) * 100).toFixed(1);

                    item.innerHTML = `
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between;">
                                <span class="agent-name">${agent}</span>
                                <span class="agent-cost">$${cost.toFixed(4)} (${percent}%)</span>
                            </div>
                            <div class="agent-bar">
                                <div class="agent-bar-fill" style="width: ${barWidth}%"></div>
                            </div>
                        </div>
                    `;

                    agentList.appendChild(item);
                });

                // Update chart
                agentChart.data.labels = sortedAgents.map(([agent, _]) => agent);
                agentChart.data.datasets[0].data = sortedAgents.map(([_, cost]) => cost);
                agentChart.update();
            }

            // Update timestamp
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }

        // Initial load
        fetch('/api/summary')
            .then(r => r.json())
            .then(data => updateDashboard(data));
    </script>
</body>
</html>
"""


class CostDashboardWeb:
    """Web-based cost dashboard using Flask."""

    def __init__(
        self,
        cost_tracker: CostTracker,
        refresh_interval: int = 5
    ):
        """
        Initialize web dashboard.

        Args:
            cost_tracker: CostTracker instance to monitor
            refresh_interval: Seconds between updates
        """
        self.tracker = cost_tracker
        self.refresh_interval = refresh_interval
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/')
        def index():
            """Render dashboard HTML."""
            return render_template_string(HTML_TEMPLATE)

        @self.app.route('/api/summary')
        def api_summary():
            """Get cost summary JSON."""
            return jsonify(self._get_dashboard_data())

        @self.app.route('/stream')
        def stream():
            """Server-Sent Events stream for live updates."""
            return Response(
                self._event_stream(),
                mimetype='text/event-stream'
            )

    def _get_dashboard_data(self) -> Dict:
        """Get current dashboard data."""
        summary = self.tracker.get_summary()

        # Calculate trends
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        hourly_summary = self.tracker.get_summary(since=one_hour_ago)
        daily_summary = self.tracker.get_summary(since=one_day_ago)

        hourly_rate = hourly_summary.total_cost_usd
        daily_projection = hourly_rate * 24

        data = {
            "summary": {
                "total_cost_usd": summary.total_cost_usd,
                "total_calls": summary.total_calls,
                "total_input_tokens": summary.total_input_tokens,
                "total_output_tokens": summary.total_output_tokens,
                "success_rate": summary.success_rate,
                "by_agent": summary.by_agent,
                "by_model": summary.by_model
            },
            "trends": {
                "hourly_rate": hourly_rate,
                "daily_projection": daily_projection,
                "last_hour_cost": hourly_summary.total_cost_usd,
                "last_day_cost": daily_summary.total_cost_usd
            }
        }

        # Add budget info if configured
        if self.tracker.budget_usd:
            data["budget"] = {
                "limit": self.tracker.budget_usd,
                "spent": summary.total_cost_usd,
                "remaining": self.tracker.budget_usd - summary.total_cost_usd,
                "percent_used": (
                    (summary.total_cost_usd / self.tracker.budget_usd * 100)
                    if self.tracker.budget_usd > 0 else 0
                )
            }

        return data

    def _event_stream(self) -> Generator[str, None, None]:
        """Generate Server-Sent Events stream."""
        while True:
            data = self._get_dashboard_data()
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(self.refresh_interval)

    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """
        Start web server.

        Args:
            host: Host to bind to
            port: Port to listen on
            debug: Enable debug mode
        """
        print(f"\n🚀 Starting Trinity Cost Dashboard")
        print(f"📊 Open http://localhost:{port} in your browser")
        print(f"🔄 Refresh interval: {self.refresh_interval} seconds")
        print(f"\nPress Ctrl+C to stop\n")

        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    """Main entry point for web dashboard CLI."""
    parser = argparse.ArgumentParser(
        description="Trinity Protocol Web Cost Dashboard"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
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
        "--interval",
        type=int,
        default=5,
        help="Refresh interval in seconds (default: 5)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    # Initialize tracker
    tracker = CostTracker(db_path=args.db, budget_usd=args.budget)

    # Create and run dashboard
    dashboard = CostDashboardWeb(
        cost_tracker=tracker,
        refresh_interval=args.interval
    )

    dashboard.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == "__main__":
    main()
