"""
Command-line interface for code generation suite.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

from .analyzer import suggest_refactors
from .test_gen import generate_tests_from_spec
from .scaffold import scaffold_module


def _write_summary(operation: str, results: List[Any], out_dir: str) -> None:
    """Write operation summary to logs."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("logs", "codegen", timestamp)
    os.makedirs(log_dir, exist_ok=True)

    # Summary data
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "total_items": len(results),
        "results": [item.__dict__ if hasattr(item, '__dict__') else item for item in results]
    }

    # Write JSON summary
    json_path = os.path.join(log_dir, "summary.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)

    # Write Markdown summary
    md_path = os.path.join(log_dir, "summary.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# CodeGen {operation.title()} Summary\n\n")
        f.write(f"**Timestamp:** {summary_data['timestamp']}\\n")
        f.write(f"**Operation:** {operation}\\n")
        f.write(f"**Total Items:** {len(results)}\\n\\n")

        if operation == "refactor":
            f.write("## Suggestions\\n\\n")
            for item in results:
                f.write(f"- **{item.path}:{item.line}** [{item.severity}] {item.rule_id}: {item.message}\\n")
        elif operation == "gen-tests":
            f.write("## Generated Tests\\n\\n")
            for item in results:
                f.write(f"- **{item.path}** ({item.ac_id}): {item.status}\\n")
        elif operation == "scaffold":
            f.write("## Created Files\\n\\n")
            for item in results:
                f.write(f"- **{item.path}** ({item.template}): {item.status}\\n")

    print(f"Summary written to: {json_path}")
    print(f"Summary written to: {md_path}")


def cmd_refactor(args: argparse.Namespace) -> int:
    """Handle refactor command."""
    import glob

    # Expand glob patterns
    paths = []
    for pattern in args.paths:
        if '*' in pattern:
            paths.extend(glob.glob(pattern, recursive=True))
        else:
            paths.append(pattern)

    # Filter to Python files only
    py_paths = [p for p in paths if p.endswith('.py') and os.path.isfile(p)]

    if not py_paths:
        print("No Python files found to analyze.", file=sys.stderr)
        return 1

    print(f"Analyzing {len(py_paths)} Python files...")

    suggestions = suggest_refactors(py_paths, args.rules)

    # Print results
    if not suggestions:
        print("No suggestions found.")
    else:
        print(f"Found {len(suggestions)} suggestions:")
        for suggestion in suggestions:
            print(f"  {suggestion.path}:{suggestion.line} [{suggestion.severity}] {suggestion.rule_id}: {suggestion.message}")

    # Write summary
    _write_summary("refactor", suggestions, "logs/codegen")

    return 0


def cmd_gen_tests(args: argparse.Namespace) -> int:
    """Handle gen-tests command."""
    if not os.path.isfile(args.spec):
        print(f"Spec file not found: {args.spec}", file=sys.stderr)
        return 1

    print(f"Generating tests from spec: {args.spec}")

    results = generate_tests_from_spec(args.spec, args.out)

    # Print results
    if not results:
        print("No tests generated.")
    else:
        print(f"Generated {len(results)} test files:")
        for result in results:
            if result.status == "created":
                print(f"  ✓ {result.path}")
            else:
                print(f"  ✗ {result.path} ({result.status})")

    # Write summary
    _write_summary("gen-tests", results, "logs/codegen")

    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    """Handle scaffold command."""
    print(f"Scaffolding {args.template} module: {args.name}")

    results = scaffold_module(args.template, args.name, args.out, args.params)

    # Print results
    if not results:
        print("No files created.")
    else:
        print(f"Created {len(results)} files:")
        for result in results:
            if result.status == "created":
                print(f"  ✓ {result.path}")
            else:
                print(f"  ✗ {result.path} ({result.status})")

    # Write summary
    _write_summary("scaffold", results, "logs/codegen")

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="codegen",
        description="Intelligent Code Generation Suite"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Refactor command
    refactor_parser = subparsers.add_parser("refactor", help="Suggest refactoring opportunities")
    refactor_parser.add_argument("--paths", nargs="+", required=True, help="File paths or patterns to analyze")
    refactor_parser.add_argument("--rules", nargs="*", help="Rules to apply (default: all basic rules)")

    # Gen-tests command
    gen_tests_parser = subparsers.add_parser("gen-tests", help="Generate test skeletons from spec")
    gen_tests_parser.add_argument("--spec", required=True, help="Path to specification file")
    gen_tests_parser.add_argument("--out", required=True, help="Output directory for tests")

    # Scaffold command
    scaffold_parser = subparsers.add_parser("scaffold", help="Create module scaffold")
    scaffold_parser.add_argument("--template", required=True, choices=["tool", "tests"], help="Template to use")
    scaffold_parser.add_argument("--name", required=True, help="Module name")
    scaffold_parser.add_argument("--out", required=True, help="Output directory")
    scaffold_parser.add_argument("--params", type=json.loads, help="Additional template parameters (JSON)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "refactor":
            return cmd_refactor(args)
        elif args.command == "gen-tests":
            return cmd_gen_tests(args)
        elif args.command == "scaffold":
            return cmd_scaffold(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())