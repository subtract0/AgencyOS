#!/usr/bin/env python3
"""Test coverage script for Agency OS.

This script runs tests with coverage analysis, generates reports, and identifies
modules with low coverage. Supports multiple output formats including HTML reports.
"""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


class TestCoverageRunner:
    """Comprehensive test coverage runner and analyzer."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.coverage_dir = self.project_root / "coverage"
        self.coverage_dir.mkdir(exist_ok=True)

    def run_tests_with_coverage(
        self,
        test_pattern: str | None = None,
        min_coverage: float = 80.0,
        include_slow: bool = False,
        parallel: bool = True,
    ) -> tuple[bool, dict]:
        """Run tests with coverage collection."""
        print("🧪 Running tests with coverage analysis...")

        # Build pytest command
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage/coverage.xml",
            "--cov-report=html:coverage/html",
            "--cov-report=json:coverage/coverage.json",
            f"--cov-fail-under={min_coverage}",
            "--tb=short",
            "-v",
        ]

        # Add test selection options
        if test_pattern:
            cmd.extend(["-k", test_pattern])

        if not include_slow:
            cmd.extend(["-m", "not slow"])

        if parallel:
            try:
                # Try to use pytest-xdist for parallel execution
                subprocess.run(
                    [sys.executable, "-c", "import xdist"], check=True, capture_output=True
                )
                import multiprocessing

                cpu_count = multiprocessing.cpu_count()
                cmd.extend(["-n", str(min(cpu_count, 4))])  # Limit to 4 workers max
            except (subprocess.CalledProcessError, ImportError):
                print("ℹ️  pytest-xdist not available, running tests sequentially")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            # Parse coverage data
            coverage_data = self._parse_coverage_results()

            success = result.returncode == 0
            return success, {
                "coverage_data": coverage_data,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            print("❌ Tests timed out after 10 minutes")
            return False, {"error": "timeout"}
        except Exception as e:
            print(f"❌ Failed to run tests: {str(e)}")
            return False, {"error": str(e)}

    def _parse_coverage_results(self) -> dict:
        """Parse coverage results from generated files."""
        coverage_data = {"total_coverage": 0.0, "files": {}, "summary": {}}

        # Try to parse JSON coverage report
        json_file = self.coverage_dir / "coverage.json"
        if json_file.exists():
            try:
                with open(json_file) as f:
                    json_data = json.load(f)

                coverage_data["total_coverage"] = json_data.get("totals", {}).get(
                    "percent_covered", 0.0
                )

                # Extract file-level coverage
                for filepath, file_data in json_data.get("files", {}).items():
                    coverage_data["files"][filepath] = {
                        "coverage": file_data.get("summary", {}).get("percent_covered", 0.0),
                        "lines_covered": file_data.get("summary", {}).get("covered_lines", 0),
                        "lines_total": file_data.get("summary", {}).get("num_statements", 0),
                        "missing_lines": file_data.get("missing_lines", []),
                    }

                coverage_data["summary"] = json_data.get("totals", {})

            except Exception as e:
                print(f"⚠️  Failed to parse JSON coverage report: {str(e)}")

        # Fallback to XML parsing if JSON failed
        elif (self.coverage_dir / "coverage.xml").exists():
            try:
                coverage_data.update(self._parse_xml_coverage())
            except Exception as e:
                print(f"⚠️  Failed to parse XML coverage report: {str(e)}")

        return coverage_data

    def _parse_xml_coverage(self) -> dict:
        """Parse coverage from XML report."""
        xml_file = self.coverage_dir / "coverage.xml"
        tree = ET.parse(xml_file)
        root = tree.getroot()

        coverage_data = {"total_coverage": 0.0, "files": {}, "summary": {}}

        # Get overall coverage
        if root.attrib.get("line-rate"):
            coverage_data["total_coverage"] = float(root.attrib["line-rate"]) * 100

        # Parse individual files
        for package in root.findall(".//package"):
            for cls in package.findall("classes/class"):
                filename = cls.get("filename", "")
                if filename:
                    line_rate = float(cls.get("line-rate", 0)) * 100
                    lines = cls.findall("lines/line")
                    total_lines = len(lines)
                    covered_lines = len([line for line in lines if line.get("hits", "0") != "0"])

                    coverage_data["files"][filename] = {
                        "coverage": line_rate,
                        "lines_covered": covered_lines,
                        "lines_total": total_lines,
                        "missing_lines": [],
                    }

        return coverage_data

    def identify_low_coverage_modules(self, threshold: float = 80.0) -> list[dict]:
        """Identify modules with coverage below threshold."""
        coverage_data = self._parse_coverage_results()
        low_coverage = []

        for filepath, file_data in coverage_data.get("files", {}).items():
            coverage = file_data.get("coverage", 0.0)
            if coverage < threshold:
                low_coverage.append(
                    {
                        "file": filepath,
                        "coverage": coverage,
                        "lines_covered": file_data.get("lines_covered", 0),
                        "lines_total": file_data.get("lines_total", 0),
                        "missing_lines": file_data.get("missing_lines", []),
                    }
                )

        # Sort by coverage percentage (lowest first)
        low_coverage.sort(key=lambda x: x["coverage"])
        return low_coverage

    def generate_coverage_report(self, include_low_coverage: bool = True) -> str:
        """Generate a comprehensive coverage report."""
        coverage_data = self._parse_coverage_results()

        report = []
        report.append("=" * 60)
        report.append("TEST COVERAGE REPORT")
        report.append("=" * 60)

        # Overall coverage
        total_coverage = coverage_data.get("total_coverage", 0.0)
        report.append(f"\n📊 OVERALL COVERAGE: {total_coverage:.1f}%")

        if total_coverage >= 90:
            report.append("✅ Excellent coverage!")
        elif total_coverage >= 80:
            report.append("✅ Good coverage")
        elif total_coverage >= 70:
            report.append("⚠️  Acceptable coverage, but could be improved")
        else:
            report.append("❌ Low coverage - needs improvement")

        # Summary statistics
        summary = coverage_data.get("summary", {})
        if summary:
            report.append("\n📈 STATISTICS:")
            report.append(f"- Total statements: {summary.get('num_statements', 'N/A')}")
            report.append(f"- Covered statements: {summary.get('covered_lines', 'N/A')}")
            report.append(f"- Missing statements: {summary.get('missing_lines', 'N/A')}")
            report.append(f"- Total branches: {summary.get('num_branches', 'N/A')}")
            report.append(f"- Covered branches: {summary.get('covered_branches', 'N/A')}")

        # Low coverage modules
        if include_low_coverage:
            low_coverage = self.identify_low_coverage_modules()
            if low_coverage:
                report.append("\n❌ MODULES WITH LOW COVERAGE (<80%):")
                report.append("-" * 40)
                for module in low_coverage[:10]:  # Show top 10
                    file_path = Path(module["file"]).name
                    coverage = module["coverage"]
                    covered = module["lines_covered"]
                    total = module["lines_total"]
                    report.append(f"{file_path}: {coverage:.1f}% ({covered}/{total} lines)")

                if len(low_coverage) > 10:
                    report.append(f"... and {len(low_coverage) - 10} more files")
            else:
                report.append("\n✅ All modules have good coverage (≥80%)")

        # File locations
        report.append("\n📁 REPORT FILES:")
        if (self.coverage_dir / "html" / "index.html").exists():
            report.append(f"- HTML report: {self.coverage_dir}/html/index.html")
        if (self.coverage_dir / "coverage.xml").exists():
            report.append(f"- XML report: {self.coverage_dir}/coverage.xml")
        if (self.coverage_dir / "coverage.json").exists():
            report.append(f"- JSON report: {self.coverage_dir}/coverage.json")

        return "\n".join(report)

    def cleanup_coverage_files(self):
        """Clean up old coverage files."""
        import shutil

        if self.coverage_dir.exists():
            shutil.rmtree(self.coverage_dir)
            self.coverage_dir.mkdir()

    def open_html_report(self):
        """Open HTML coverage report in browser."""
        html_file = self.coverage_dir / "html" / "index.html"
        if html_file.exists():
            import webbrowser

            webbrowser.open(f"file://{html_file.absolute()}")
            print(f"🌐 Opened coverage report in browser: {html_file}")
        else:
            print("❌ HTML coverage report not found. Run tests with coverage first.")


def main():
    """Main entry point for the coverage script."""
    parser = argparse.ArgumentParser(description="Run tests with coverage analysis")
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=80.0,
        help="Minimum coverage percentage required (default: 80.0)",
    )
    parser.add_argument(
        "--test-pattern", type=str, help="Pattern to select specific tests (pytest -k pattern)"
    )
    parser.add_argument(
        "--include-slow", action="store_true", help="Include slow tests in coverage run"
    )
    parser.add_argument(
        "--no-parallel", action="store_true", help="Disable parallel test execution"
    )
    parser.add_argument(
        "--html", action="store_true", help="Open HTML coverage report in browser after completion"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean up old coverage files before running"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate report from existing coverage data",
    )

    args = parser.parse_args()

    runner = TestCoverageRunner()

    try:
        if args.clean:
            print("🧹 Cleaning up old coverage files...")
            runner.cleanup_coverage_files()

        if not args.report_only:
            # Run tests with coverage
            success, results = runner.run_tests_with_coverage(
                test_pattern=args.test_pattern,
                min_coverage=args.min_coverage,
                include_slow=args.include_slow,
                parallel=not args.no_parallel,
            )

            if not success:
                print("❌ Tests failed or coverage below threshold")
                if "stdout" in results:
                    print("\nTest output:")
                    print(results["stdout"])
                if "stderr" in results:
                    print("\nError output:")
                    print(results["stderr"])
                return 1

        # Generate and display report
        report = runner.generate_coverage_report()
        print("\n" + report)

        # Save report to file
        report_file = runner.coverage_dir / "coverage_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")

        # Open HTML report if requested
        if args.html:
            runner.open_html_report()

        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Coverage run interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error during coverage run: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
