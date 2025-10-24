#!/usr/bin/env python3
"""
Deduplicate extracted JSON examples and maintain provenance tracking.

Usage:
    python scripts/dedupe_and_provenance.py data/seed.jsonl data/seed.dedup.jsonl

Outputs:
    - data/seed.dedup.jsonl: Deduplicated examples
    - data/provenance_manifest.json: Checksums + line numbers for traceability
"""
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


def compute_content_hash(obj: dict) -> str:
    """
    Compute stable hash of instruction content (ignoring metadata variations).

    Uses only instruction/prompt/output fields for deduplication.
    """
    # Extract core content fields (ignore id, timestamps, etc.)
    instruction = obj.get("instruction", "")
    prompt = obj.get("prompt", "")
    output = obj.get("output", "")
    input_field = str(obj.get("input", ""))

    # Canonical string for hashing
    content = f"{instruction}||{prompt}||{output}||{input_field}"

    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def dedupe_with_provenance(input_path: Path, output_path: Path) -> Tuple[int, int, Dict]:
    """
    Deduplicate JSONL file and generate provenance manifest.

    Returns:
        (original_count, deduped_count, provenance_manifest)
    """
    seen_hashes: Dict[str, int] = {}  # hash -> first line number
    duplicates: Dict[int, str] = {}  # line number -> duplicate of line X
    deduped_objects: List[dict] = []

    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                obj = json.loads(line)
                content_hash = compute_content_hash(obj)

                if content_hash in seen_hashes:
                    # Duplicate found
                    original_line = seen_hashes[content_hash]
                    duplicates[line_num] = f"duplicate of line {original_line}"
                else:
                    # First occurrence
                    seen_hashes[content_hash] = line_num

                    # Add provenance metadata
                    obj["_provenance"] = {
                        "original_line": line_num,
                        "content_hash": content_hash,
                        "source_file": str(input_path)
                    }

                    deduped_objects.append(obj)

            except json.JSONDecodeError as e:
                print(f"Warning: Malformed JSON at line {line_num}: {e}", file=sys.stderr)
                duplicates[line_num] = f"malformed JSON: {e}"

    # Write deduplicated objects
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for obj in deduped_objects:
            json.dump(obj, f, ensure_ascii=False)
            f.write('\n')

    # Generate provenance manifest
    provenance_manifest = {
        "source_file": str(input_path),
        "output_file": str(output_path),
        "original_count": line_num,
        "deduped_count": len(deduped_objects),
        "duplicates_removed": len(duplicates),
        "duplicate_map": {str(k): v for k, v in duplicates.items()},
        "hash_to_line": {h: ln for h, ln in seen_hashes.items()}
    }

    # Write manifest
    manifest_path = output_path.parent / "provenance_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(provenance_manifest, f, indent=2)

    print(f"✅ Deduplication complete:")
    print(f"   Original: {line_num} objects")
    print(f"   Deduped: {len(deduped_objects)} objects")
    print(f"   Duplicates removed: {len(duplicates)}")
    print(f"   Provenance manifest: {manifest_path}")

    return line_num, len(deduped_objects), provenance_manifest


def main():
    if len(sys.argv) < 3:
        print("Usage: python dedupe_and_provenance.py input.jsonl output.jsonl")
        sys.exit(2)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    dedupe_with_provenance(input_path, output_path)


if __name__ == "__main__":
    main()
