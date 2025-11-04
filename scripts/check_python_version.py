#!/usr/bin/env python3
"""
Python 3.12 LTS Version Enforcement

Constitutional Compliance:
- Article II: 100% Verification (enforce Python 3.12 standard)
- Article III: Automated Enforcement (block commits with wrong version)

Mars Rover Reliability: ONE Python version across ALL environments.
"""

import sys

REQUIRED_MAJOR = 3
REQUIRED_MINOR = 12

def check_python_version() -> int:
    """
    Verify Python 3.12 is being used.

    Returns:
        0 if Python 3.12, 1 otherwise
    """
    current_major = sys.version_info.major
    current_minor = sys.version_info.minor

    if current_major != REQUIRED_MAJOR or current_minor != REQUIRED_MINOR:
        print(f"❌ PYTHON VERSION ERROR")
        print(f"")
        print(f"Required: Python {REQUIRED_MAJOR}.{REQUIRED_MINOR}.x (LTS)")
        print(f"Current:  Python {current_major}.{current_minor}.{sys.version_info.micro}")
        print(f"")
        print(f"🔧 Fix: Use Python 3.12 LTS for Mars rover-level reliability")
        print(f"")
        print(f"   # Activate pyenv Python 3.12")
        print(f"   pyenv global 3.12.12")
        print(f"")
        print(f"   # Recreate venv")
        print(f"   rm -rf .venv && python -m venv .venv")
        print(f"   .venv/bin/pip install -e .")
        print(f"")
        print(f"Constitutional Compliance: Article II + III (zero version chaos)")
        return 1

    print(f"✅ Python version check passed: {current_major}.{current_minor}.{sys.version_info.micro}")
    return 0


if __name__ == "__main__":
    sys.exit(check_python_version())
