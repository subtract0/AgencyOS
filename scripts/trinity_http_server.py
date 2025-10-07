#!/usr/bin/env python3
"""Trinity HTTP Server - Serve Trinity Auditor via HTTP API for GitHub Actions.

This server runs on your M4 Mac and exposes Trinity Auditor as an HTTP endpoint.
GitHub Actions can trigger audits by sending HTTP requests to this server.

Usage:
    python scripts/trinity_http_server.py --port 8765

    # With ngrok for external access:
    ngrok http 8765
"""

import argparse
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for external requests

# Repository root
REPO_ROOT = Path(__file__).parent.parent


@app.route("/", methods=["GET"])
def health_check() -> dict[str, str | dict]:
    """Health check endpoint."""
    return jsonify(
        {
            "status": "ok",
            "service": "Trinity HTTP Server",
            "version": "1.0.0",
            "endpoints": {
                "/audit": "POST - Trigger Trinity audit on a repository",
                "/status": "GET - Check server status",
            },
        }
    )


@app.route("/status", methods=["GET"])
def status() -> dict[str, Any]:
    """Server status endpoint."""
    return jsonify(
        {
            "server": "running",
            "repo_root": str(REPO_ROOT),
            "auditor_available": (REPO_ROOT / "scripts/continuous_audit_m4pro.py").exists(),
            "dashboard_available": (REPO_ROOT / "scripts/generate_review_dashboard.py").exists(),
        }
    )


@app.route("/audit", methods=["POST"])
def audit_repository() -> tuple[dict[str, Any], int]:
    """
    Trigger Trinity audit on a GitHub repository.

    Expected JSON payload:
    {
        "repo": "owner/repo-name",
        "pr": 123,
        "sha": "abc123def456",
        "branch": "feature-branch" (optional)
    }

    Returns:
        JSON response with audit results and recommendations.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400

        repo = data.get("repo")
        pr_number = data.get("pr")
        sha = data.get("sha")
        branch = data.get("branch", f"pr-{pr_number}")

        if not repo or not pr_number:
            return jsonify({"error": "Missing required fields: repo, pr"}), 400

        logger.info(f"Audit request: {repo} PR#{pr_number} SHA:{sha}")

        # Create temporary directory for clone
        with tempfile.TemporaryDirectory() as tmpdir:
            clone_dir = Path(tmpdir) / "repo"

            # Clone repository
            logger.info(f"Cloning {repo}...")
            clone_result = subprocess.run(
                ["git", "clone", f"https://github.com/{repo}.git", str(clone_dir)],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if clone_result.returncode != 0:
                return jsonify(
                    {
                        "error": "Failed to clone repository",
                        "details": clone_result.stderr,
                    }
                ), 500

            # Checkout PR branch
            logger.info(f"Checking out {branch}...")
            checkout_result = subprocess.run(
                ["git", "fetch", "origin", f"pull/{pr_number}/head:{branch}"],
                cwd=clone_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if checkout_result.returncode == 0:
                subprocess.run(["git", "checkout", branch], cwd=clone_dir, check=True)
            else:
                logger.warning(f"Could not fetch PR branch, using default branch")

            # Run Trinity Auditor
            logger.info("Running Trinity Auditor...")
            audit_result = subprocess.run(
                [
                    "python",
                    str(REPO_ROOT / "scripts/continuous_audit_m4pro.py"),
                    "--dir",
                    str(clone_dir),
                    "--mode",
                    "once",
                    "--output-dir",
                    str(clone_dir / ".trinity-output"),
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes max
            )

            # Parse audit results
            audit_output_dir = clone_dir / ".trinity-output/audit_recommendations"
            recommendations = []

            if audit_output_dir.exists():
                for rec_file in audit_output_dir.glob("*.md"):
                    try:
                        with open(rec_file) as f:
                            content = f.read()
                            # Simple parsing - extract metadata from markdown
                            recommendations.append(
                                {
                                    "file": rec_file.name,
                                    "content": content[:500],  # First 500 chars
                                }
                            )
                    except Exception as e:
                        logger.warning(f"Could not parse {rec_file}: {e}")

            # Generate dashboard
            dashboard_text = ""
            try:
                dashboard_result = subprocess.run(
                    [
                        "python",
                        str(REPO_ROOT / "scripts/format_pr_comment.py"),
                        "--input",
                        str(clone_dir / ".trinity-output/audit_recommendations/.audit_state.json"),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if dashboard_result.returncode == 0:
                    dashboard_text = dashboard_result.stdout
            except Exception as e:
                logger.warning(f"Dashboard generation failed: {e}")

            # Return results
            response = {
                "status": "success",
                "repo": repo,
                "pr": pr_number,
                "sha": sha,
                "recommendations_count": len(recommendations),
                "recommendations": recommendations[:10],  # First 10 for brevity
                "dashboard": dashboard_text,
                "auto_fix_available": len(recommendations) > 0,
            }

            logger.info(f"Audit complete: {len(recommendations)} recommendations")
            return jsonify(response), 200

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Audit timed out (5 minutes limit)"}), 504
    except Exception as e:
        logger.error(f"Audit failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def main():
    """Start Trinity HTTP server."""
    parser = argparse.ArgumentParser(description="Trinity HTTP Server")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    logger.info(f"Starting Trinity HTTP Server on {args.host}:{args.port}")
    logger.info(f"Repository root: {REPO_ROOT}")
    logger.info("Endpoints available:")
    logger.info("  GET  / - Health check")
    logger.info("  GET  /status - Server status")
    logger.info("  POST /audit - Trigger repository audit")

    if args.debug:
        logger.warning("Debug mode enabled - DO NOT use in production")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
