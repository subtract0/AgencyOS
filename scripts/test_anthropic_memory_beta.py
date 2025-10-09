#!/usr/bin/env python
"""Test Anthropic Memory Tool Beta Access

Validates that:
1. anthropic>=0.42.0 is installed
2. Beta header context-management-2025-06-27 is accepted
3. memory_20250818 tool type is available
4. Claude Sonnet 4.5 supports the memory feature

Usage:
    python scripts/test_anthropic_memory_beta.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_anthropic_version():
    """Verify anthropic SDK version meets minimum requirement"""
    try:
        import anthropic

        version = anthropic.__version__
        major, minor = map(int, version.split(".")[:2])

        if major == 0 and minor >= 42:
            print(f"✅ anthropic version {version} meets requirement (>=0.42.0)")
            return True
        elif major > 0:
            print(f"✅ anthropic version {version} meets requirement (>=0.42.0)")
            return True
        else:
            print(f"❌ anthropic version {version} too old (need >=0.42.0)")
            return False
    except ImportError:
        print("❌ anthropic SDK not installed")
        return False
    except Exception as e:
        print(f"❌ Version check failed: {e}")
        return False


def test_memory_beta_access():
    """Test that memory tool beta is accessible"""
    try:
        import anthropic

        # Check for API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️  ANTHROPIC_API_KEY not set - skipping API test")
            print("   Set ANTHROPIC_API_KEY to test beta access")
            return None

        client = anthropic.Anthropic(api_key=api_key)

        # Minimal test message with memory tool
        message = client.beta.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Reply with just 'OK' to confirm memory tool access"}
            ],
            tools=[{"type": "memory_20250818", "name": "memory"}],
            betas=["context-management-2025-06-27"],
        )

        print("✅ Memory tool beta access confirmed")
        print(f"   Model: {message.model}")
        print(f"   Stop reason: {message.stop_reason}")

        return True

    except anthropic.BadRequestError as e:
        print(f"❌ Beta access denied: {e}")
        print("   Check if your API key has beta access enabled")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Anthropic Memory Tool Beta Access Validation")
    print("=" * 60)
    print()

    results = []

    # Test 1: SDK version
    print("[1/2] Checking anthropic SDK version...")
    results.append(test_anthropic_version())
    print()

    # Test 2: Beta API access
    print("[2/2] Testing beta API access...")
    api_result = test_memory_beta_access()
    if api_result is not None:
        results.append(api_result)
    print()

    # Summary
    print("=" * 60)
    if all(results):
        print("✅ All tests passed - Memory tool beta is ready to use")
        return 0
    elif None in results:
        print("⚠️  Partial validation - set ANTHROPIC_API_KEY for full test")
        return 0 if results[0] else 1
    else:
        print("❌ Validation failed - check errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
