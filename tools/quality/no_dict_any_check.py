#!/usr/bin/env python3
"""
AST-based checker to forbid Dict[str, Any] and dict[str, Any] in code.

- Scans all .py files under the repository (excluding common vendor/test fixtures if needed)
- Flags only type annotations (function args/returns, AnnAssign, variable annotations)
- Ignores comments and docstrings; robust against false positives

Exit codes:
- 0 when clean
- 1 when violations are found (prints a summary and file:line:col entries)

Optional environment variables:
- NO_DICT_ANY_ALLOWLIST: comma-separated file globs to ignore (rare, temporary)
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from fnmatch import fnmatch
from typing import Iterable, List, Tuple

# Patterns to scan
DEFAULT_INCLUDE = "**/*.py"
DEFAULT_EXCLUDE_DIRS = {".git", ".venv", "venv", "build", "dist", "node_modules", "__pycache__"}

AllowList = Tuple[str, ...]


def _iter_files(root: Path, allowlist: AllowList) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        if any(part in DEFAULT_EXCLUDE_DIRS for part in p.parts):
            continue
        if allowlist and any(fnmatch(str(p), pat) for pat in allowlist):
            continue
        yield p


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _is_attr_any(node: ast.AST) -> bool:
    # typing.Any or typing_extensions.Any, etc.
    return isinstance(node, ast.Attribute) and node.attr == "Any"


def _is_any(node: ast.AST) -> bool:
    return _is_name(node, "Any") or _is_attr_any(node)


def _is_str_name(node: ast.AST) -> bool:
    return _is_name(node, "str")


def _match_dict_str_any(sub: ast.Subscript) -> bool:
    # Match Dict[str, Any] and dict[str, Any]
    # sub.value: Name(id='Dict'|'dict') or Attribute
    base_ok = False
    if isinstance(sub.value, ast.Name) and sub.value.id in {"Dict", "dict"}:
        base_ok = True
    elif isinstance(sub.value, ast.Attribute) and sub.value.attr in {"Dict", "dict"}:
        base_ok = True
    if not base_ok:
        return False

    # Extract slice arguments (key, value)
    sl = sub.slice
    # Python 3.9+: slice can be ast.Tuple or ast.Subscript for complex types
    if isinstance(sl, ast.Tuple) and len(sl.elts) == 2:
        key_node, val_node = sl.elts
    else:
        # In some versions, Subscript.slice may be ast.Index or a single node; skip uncertain cases
        return False

    return _is_str_name(key_node) and _is_any(val_node)


def _collect_violations(tree: ast.AST, filename: str) -> List[Tuple[int, int, str]]:
    violations: List[Tuple[int, int, str]] = []

    class Visitor(ast.NodeVisitor):
        def visit_AnnAssign(self, node: ast.AST) -> None:  # type: ignore[override]
            ann = getattr(node, "annotation", None)
            if isinstance(ann, ast.Subscript) and _match_dict_str_any(ann):
                violations.append((node.lineno, node.col_offset, "annotation"))
            self.generic_visit(node)

        def visit_arg(self, node: ast.arg) -> None:
            if isinstance(node.annotation, ast.Subscript) and _match_dict_str_any(node.annotation):
                violations.append((node.lineno, node.col_offset, "arg"))
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            # Return type
            if isinstance(node.returns, ast.Subscript) and _match_dict_str_any(node.returns):
                violations.append((node.returns.lineno, node.returns.col_offset, "return"))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            if isinstance(node.returns, ast.Subscript) and _match_dict_str_any(node.returns):
                violations.append((node.returns.lineno, node.returns.col_offset, "return"))
            self.generic_visit(node)

    Visitor().visit(tree)
    return violations


def main() -> int:
    repo_root = Path(os.getenv("GITHUB_WORKSPACE", Path.cwd()))
    allow_env = os.getenv("NO_DICT_ANY_ALLOWLIST", "").strip()
    allowlist: AllowList = tuple(p.strip() for p in allow_env.split(",") if p.strip())

    total = 0
    files_with = 0
    entries: List[str] = []

    for py in _iter_files(repo_root, allowlist):
        try:
            src = py.read_text(encoding="utf-8")
        except Exception:
            continue
        try:
            tree = ast.parse(src, filename=str(py))
        except SyntaxError:
            # Skip files with syntax errors
            continue

        vios = _collect_violations(tree, str(py))
        if vios:
            files_with += 1
            for ln, col, kind in vios:
                total += 1
                entries.append(f"{py}:{ln}:{col}: forbids Dict[str, Any]/dict[str, Any] in {kind}")

    if total:
        print("Found forbidden Dict[str, Any]/dict[str, Any] usages:")
        for e in entries:
            print(e)
        print(f"Summary: {total} violations in {files_with} files")
        return 1
    else:
        print("No Dict[str, Any]/dict[str, Any] found in code annotations. ✅")
        return 0


if __name__ == "__main__":
    sys.exit(main())
