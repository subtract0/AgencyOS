#!/usr/bin/env python3
"""
Clean JSON contamination from training examples.

Issues to fix:
1. Remove (NNN) prefix from instruction field
2. Remove embedded escaped JSON fragments (\",\"input\":\"\",\"output\":\")
3. Clean output field (remove Abstract\":\" prefix)
4. Validate cleaned JSON is parseable

Usage:
    python scripts/clean_json_contamination.py data/seed.dedup.jsonl data/seed.dedup.clean.jsonl
"""
import sys
import json
import re
from pathlib import Path
from typing import Dict, Tuple


def clean_instruction(instruction: str) -> str:
    """
    Clean instruction field:
    - Remove (NNN) prefix
    - Remove embedded JSON fragments
    """
    # Remove (NNN) prefix (e.g., "(497) " or "(1102) ")
    cleaned = re.sub(r'^\(\d+\)\s*', '', instruction)

    # Remove embedded escaped JSON fragments
    # Pattern: ...\",\"input\":\"\",\"output\":\"...
    cleaned = re.sub(r'\\",' + r'\\"input\\":\\"\\",\\"output\\":\\"', '', cleaned)

    # Also handle unescaped version
    cleaned = re.sub(r'","input":"","output":"', '', cleaned)

    return cleaned.strip()


def clean_output(output: str) -> str:
    """
    Clean output field:
    - Remove Abstract\":\" prefix
    - Remove other malformed prefixes
    """
    # Remove Abstract\":\" prefix
    cleaned = re.sub(r'^Abstract\\":\\"', '', output)
    cleaned = re.sub(r'^Abstract":"', '', cleaned)

    return cleaned.strip()


def clean_json_object(obj: Dict) -> Dict:
    """
    Clean a single JSON object.
    """
    cleaned = obj.copy()

    # Clean instruction field
    instruction = obj.get('instruction', obj.get('prompt', ''))
    if instruction:
        cleaned['instruction'] = clean_instruction(instruction)
        if 'prompt' in cleaned and 'instruction' not in obj:
            cleaned['prompt'] = cleaned['instruction']
            del cleaned['instruction']

    # Clean output field
    output = obj.get('output', obj.get('response', ''))
    if output:
        cleaned['output'] = clean_output(output)
        if 'response' in cleaned and 'output' not in obj:
            cleaned['response'] = cleaned['output']
            del cleaned['output']

    return cleaned


def clean_jsonl_file(input_path: Path, output_path: Path) -> Tuple[int, int, int]:
    """
    Clean JSONL file.

    Returns:
        (total_lines, cleaned_lines, error_lines)
    """
    total = 0
    cleaned = 0
    errors = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(input_path, 'r') as fin, open(output_path, 'w') as fout:
        for line_num, line in enumerate(fin, 1):
            if not line.strip():
                continue

            total += 1

            try:
                # Load original JSON
                obj = json.loads(line)

                # Clean it
                cleaned_obj = clean_json_object(obj)

                # Write cleaned JSON
                json.dump(cleaned_obj, fout, ensure_ascii=False)
                fout.write('\n')

                cleaned += 1

            except json.JSONDecodeError as e:
                print(f"Warning: Malformed JSON at line {line_num}: {e}", file=sys.stderr)
                errors += 1
            except Exception as e:
                print(f"Error processing line {line_num}: {e}", file=sys.stderr)
                errors += 1

    return total, cleaned, errors


def verify_cleaning(file_path: Path) -> Tuple[int, int]:
    """
    Verify cleaned file has no contamination.

    Returns:
        (total_lines, contaminated_lines)
    """
    contaminated = 0
    total = 0

    with open(file_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue

            total += 1

            try:
                obj = json.loads(line)
                instruction = obj.get('instruction', obj.get('prompt', ''))
                output = obj.get('output', obj.get('response', ''))

                # Check for contamination patterns
                if re.match(r'^\(\d+\)', instruction):
                    contaminated += 1
                elif '","input":"' in instruction:
                    contaminated += 1
                elif 'Abstract":"' in output:
                    contaminated += 1

            except json.JSONDecodeError:
                contaminated += 1

    return total, contaminated


def main():
    if len(sys.argv) < 3:
        print("Usage: python clean_json_contamination.py input.jsonl output.jsonl")
        sys.exit(2)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Cleaning {input_path} → {output_path}")
    print("=" * 70)

    # Clean file
    total, cleaned, errors = clean_jsonl_file(input_path, output_path)

    print(f"\nCleaning Results:")
    print(f"  Total lines: {total}")
    print(f"  Cleaned: {cleaned}")
    print(f"  Errors: {errors}")

    # Verify
    print(f"\nVerifying cleaned file...")
    total_verify, contaminated = verify_cleaning(output_path)

    print(f"  Total lines: {total_verify}")
    print(f"  Contaminated: {contaminated}")

    if contaminated == 0:
        print(f"\n✅ SUCCESS: No contamination detected!")
    else:
        print(f"\n⚠️  WARNING: {contaminated} lines still contaminated")
        print(f"   Manual review may be needed")


if __name__ == "__main__":
    main()
