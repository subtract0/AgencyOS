#!/usr/bin/env python3
"""
Feature Inventory Script

Reads FEATURES.md and checks for corresponding test files to provide
a compact report of feature coverage.
"""

import re
from pathlib import Path


def extract_features_from_md(features_file):
    """Extract features and test files from FEATURES.md"""
    with open(features_file, 'r') as f:
        content = f.read()

    # Find all test coverage references
    test_pattern = r'\*\*Test Coverage\*\*:\s*`([^`]+)`'
    test_files = re.findall(test_pattern, content)

    # Find feature sections (## or ### headings)
    feature_pattern = r'^#{2,3}\s+(.+)$'
    feature_matches = re.findall(feature_pattern, content, re.MULTILINE)

    return feature_matches, test_files


def check_test_files(test_files, project_root):
    """Check which test files exist and count test functions"""
    coverage_report = {}

    for test_file in test_files:
        full_path = project_root / test_file
        exists = full_path.exists()
        test_count = 0

        if exists:
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    # Count test functions
                    test_count = len(re.findall(r'def test_', content))
            except Exception:
                test_count = -1

        coverage_report[test_file] = {
            'exists': exists,
            'test_count': test_count
        }

    return coverage_report


def main():
    """Generate feature coverage report"""
    project_root = Path(__file__).parent.parent
    features_file = project_root / "FEATURES.md"

    if not features_file.exists():
        print("❌ FEATURES.md not found")
        return

    print("🔍 Agency Code Feature Inventory\n")

    # Extract features and test files
    features, test_files = extract_features_from_md(features_file)
    coverage_report = check_test_files(test_files, project_root)

    # Summary stats
    total_tests = len(test_files)
    existing_tests = sum(1 for r in coverage_report.values() if r['exists'])
    total_test_functions = sum(r['test_count'] for r in coverage_report.values() if r['test_count'] > 0)

    print("📊 Summary:")
    print(f"   Features documented: {len(features)}")
    print(f"   Test files referenced: {total_tests}")
    print(f"   Test files found: {existing_tests}/{total_tests}")
    print(f"   Total test functions: {total_test_functions}")
    print()

    # Coverage details
    print("📋 Test Coverage Details:")
    for test_file, report in sorted(coverage_report.items()):
        status = "✅" if report['exists'] else "❌"
        count = f"({report['test_count']} tests)" if report['test_count'] > 0 else ""
        print(f"   {status} {test_file} {count}")

    print()
    coverage_pct = (existing_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"🎯 Overall Coverage: {coverage_pct:.1f}%")


if __name__ == "__main__":
    main()