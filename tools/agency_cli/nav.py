from __future__ import annotations

import ast
import fnmatch
import os
import re
from typing import Iterable, List


def _iter_files(root: str, pattern: str) -> Iterable[str]:
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            rel = os.path.relpath(os.path.join(dirpath, f), root)
            if fnmatch.fnmatch(rel, pattern):
                yield os.path.join(root, rel)


def list_dir(path: str) -> List[str]:
    if not os.path.isdir(path):
        return [path]
    entries = sorted(os.listdir(path))
    return entries


def print_tree(path: str, depth: int = 2) -> None:
    base = os.path.abspath(path)
    for dirpath, dirnames, filenames in os.walk(base):
        level = os.path.relpath(dirpath, base).count(os.sep)
        if level >= depth:
            continue
        indent = "  " * level
        print(f"{indent}{os.path.basename(dirpath)}/")
        for f in sorted(filenames):
            print(f"{indent}  {f}")


def open_file_segment(path: str, start: int = 1, end: int | None = None) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    s = max(start - 1, 0)
    e = len(lines) if end is None else min(end, len(lines))
    out = []
    for i in range(s, e):
        out.append(f"{i+1:5d}: {lines[i].rstrip()}\n")
    return "".join(out)


def grep_search(root: str, pattern: str, glob: str = "**/*.py") -> List[str]:
    rx = re.compile(pattern)
    matches: List[str] = []
    for path in _iter_files(root, glob):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, start=1):
                    if rx.search(line):
                        rel = os.path.relpath(path, root)
                        matches.append(f"{rel}:{i}:{line.rstrip()}")
        except Exception:
            continue
    return matches


def find_files(root: str, pattern: str) -> List[str]:
    files = [os.path.relpath(p, root) for p in _iter_files(root, pattern)]
    return sorted(files)


def extract_symbols(path: str) -> List[str]:
    """Extract Python symbols (classes and functions) under path (file or directory)."""
    results: List[str] = []
    def _extract_file(pyfile: str) -> None:
        try:
            with open(pyfile, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=pyfile)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    results.append(f"{pyfile}:{getattr(node, 'lineno', 1)}:{node.__class__.__name__} {node.name}")
        except Exception:
            pass

    if os.path.isdir(path):
        for p in _iter_files(path, "**/*.py"):
            _extract_file(p)
    else:
        _extract_file(path)

    # Relativize
    root = os.path.abspath(os.getcwd())
    rels = []
    for r in results:
        try:
            filepart, rest = r.split(":", 1)
            rels.append(f"{os.path.relpath(filepart, root)}:{rest}")
        except ValueError:
            rels.append(r)
    return sorted(rels)


def find_references(root: str, name: str, glob: str = "**/*.py") -> List[str]:
    # Simple word-boundary search
    rx = re.compile(rf"\b{re.escape(name)}\b")
    matches: List[str] = []
    for path in _iter_files(root, glob):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, start=1):
                    if rx.search(line):
                        rel = os.path.relpath(path, root)
                        matches.append(f"{rel}:{i}:{line.rstrip()}")
        except Exception:
            continue
    return matches