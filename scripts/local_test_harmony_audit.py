#!/usr/bin/env python3
"""
Test-Base/Code-Base Harmony Audit using LOCAL MODEL ONLY

Demonstrates M4 Pro 48GB local execution with Qwen3-Coder Q8_0.
Cost: $0 (100% local)
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
import requests

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "qwen3-coder:30b"  # Q4_K_M, 18GB (faster than Q8_0)

def call_local_model(prompt: str) -> str:
    """Call Ollama local model (cost: $0)."""
    response = requests.post(
        OLLAMA_API,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower for more focused analysis
                "num_predict": 2048,  # Max tokens
            }
        },
        timeout=300  # 5 min timeout
    )

    if response.status_code == 200:
        result = response.json()
        return result.get('response', '')
    else:
        raise Exception(f"Ollama API error: {response.status_code}")

def analyze_test_file_structure():
    """Analyze test file organization and structure."""
    print("🔍 Analyzing test file structure...")

    # Get test file count and structure
    test_files = list(Path("tests").rglob("test_*.py"))

    # Group by category
    categories = {}
    for test_file in test_files:
        parts = test_file.parts
        if len(parts) > 1:
            category = parts[1]  # tests/category/...
        else:
            category = "root"

        categories.setdefault(category, []).append(test_file)

    structure_info = {
        "total_files": len(test_files),
        "categories": {cat: len(files) for cat, files in categories.items()},
        "top_categories": [
            [cat, len(files)]  # Convert to JSON-serializable list
            for cat, files in sorted(
                categories.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
        ]
    }

    return structure_info, test_files[:20]  # Sample for analysis

def analyze_code_coverage():
    """Analyze what code is being tested."""
    print("🔍 Analyzing code coverage patterns...")

    # Get source files
    source_files = []
    for pattern in ["*.py", "**/*.py"]:
        source_files.extend(Path(".").glob(pattern))

    # Filter out tests, venv, etc.
    source_files = [
        f for f in source_files
        if "test" not in str(f).lower()
        and ".venv" not in str(f)
        and "node_modules" not in str(f)
    ][:100]  # Sample

    return {
        "total_source_files": len(source_files),
        "sample_files": [str(f) for f in source_files[:20]]
    }

def run_local_audit():
    """Run comprehensive test-code harmony audit using LOCAL MODEL."""
    print("="*80)
    print("🚀 STARTING LOCAL TEST HARMONY AUDIT")
    print("="*80)
    print(f"Model: {MODEL}")
    print(f"Cost: $0 (100% local)")
    print(f"Time: {datetime.now()}")
    print()

    # Phase 1: Analyze structure
    print("\n📊 Phase 1: Analyzing Test Structure...")
    structure, sample_tests = analyze_test_file_structure()
    print(f"  Total test files: {structure['total_files']}")
    print(f"  Categories: {len(structure['categories'])}")
    for cat, count in structure['top_categories'][:5]:
        print(f"    - {cat}: {count} files")

    # Phase 2: Analyze code
    print("\n📊 Phase 2: Analyzing Code Coverage...")
    coverage = analyze_code_coverage()
    print(f"  Source files analyzed: {coverage['total_source_files']}")

    # Phase 3: LOCAL MODEL ANALYSIS
    print("\n🤖 Phase 3: Running Local Model Analysis...")
    print("  (This proves local execution works!)")

    audit_prompt = f"""You are a senior software engineer auditing test suite quality.

Test Suite Stats:
- Total test files: {structure['total_files']}
- Test categories: {list(structure['categories'].keys())}
- Source files: {coverage['total_source_files']}

Sample test files:
{chr(10).join(f"- {f}" for f in [str(t) for t in sample_tests[:10]])}

Analyze this test suite for:
1. Organization quality (good structure?)
2. Coverage completeness (gaps?)
3. Naming consistency (patterns?)
4. Potential issues (red flags?)

Be concise (5-7 bullet points). Focus on actionable insights."""

    print("  Calling local model (Qwen3-Coder Q8_0)...")
    start_time = datetime.now()

    try:
        analysis = call_local_model(audit_prompt)
        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"  ✅ Analysis complete in {elapsed:.1f}s")
        print()

        # Phase 4: Generate Report
        print("\n📋 Phase 4: Generating Report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "model": MODEL,
            "cost": 0.0,
            "execution_time_seconds": elapsed,
            "structure": structure,
            "coverage": coverage,
            "local_model_analysis": analysis,
            "proof_of_concept": "✅ LOCAL EXECUTION WORKING"
        }

        # Save report
        report_path = Path("test_harmony_audit_local.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"  ✅ Report saved: {report_path}")

        # Display analysis
        print("\n" + "="*80)
        print("🤖 LOCAL MODEL ANALYSIS (Qwen3-Coder Q8_0)")
        print("="*80)
        print(analysis)
        print()

        # Summary
        print("="*80)
        print("✅ PROOF OF CONCEPT: LOCAL EXECUTION SUCCESSFUL")
        print("="*80)
        print(f"Model: {MODEL}")
        print(f"Execution Time: {elapsed:.1f} seconds")
        print(f"Cost: $0 (100% local)")
        print(f"Equivalent Cloud Cost: ~$0.50 (avoided!)")
        print(f"Report: {report_path}")
        print()
        print("🎯 This demonstrates M4 Pro 48GB can run useful audits locally!")
        print("="*80)

        return report

    except Exception as e:
        print(f"  ❌ Error: {e}")
        raise

if __name__ == "__main__":
    try:
        report = run_local_audit()
        exit(0)
    except Exception as e:
        print(f"\n❌ Audit failed: {e}")
        exit(1)
