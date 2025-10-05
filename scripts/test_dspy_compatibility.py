#!/usr/bin/env python3
"""DSPy backward compatibility validation.

This script validates that DSPy dependencies are correctly installed
and can be imported without errors. It's designed to be non-blocking
for CI pipelines while providing visibility into DSPy availability.
"""
import sys
from pathlib import Path


def test_dspy_installation():
    """Validate DSPy core framework is installed."""
    try:
        import dspy
        print(f"✅ DSPy {dspy.__version__} installed successfully")
        return True
    except ImportError as e:
        print(f"⚠️  DSPy not installed (optional dependency): {e}")
        return False


def test_dspy_dependencies():
    """Validate DSPy-related dependencies."""
    dependencies = {
        "sentence_transformers": "Sentence transformers for embeddings",
        "faiss": "FAISS for vector similarity search",
        "optuna": "Optuna for hyperparameter optimization",
        "mlflow": "MLflow for experiment tracking",
    }

    results = {}
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
            results[package] = True
        except ImportError:
            print(f"⚠️  {package} not available: {description}")
            results[package] = False

    return results


def test_dspy_agents_importable():
    """Validate DSPy agents can be imported."""
    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from dspy_agents.modules.code_agent import DSPyCodeAgent
        print("✅ DSPy agents are importable")
        return True
    except ImportError as e:
        print(f"⚠️  DSPy agents not importable: {e}")
        return False


def main():
    """Run all compatibility checks."""
    print("=" * 60)
    print("DSPy Compatibility Check")
    print("=" * 60)

    dspy_installed = test_dspy_installation()
    print()

    if dspy_installed:
        print("Checking DSPy dependencies...")
        dep_results = test_dspy_dependencies()
        print()

        print("Checking DSPy agents...")
        agents_ok = test_dspy_agents_importable()
        print()

        # Calculate success rate
        total_checks = len(dep_results) + 2  # deps + dspy + agents
        successful = sum(dep_results.values()) + 1 + (1 if agents_ok else 0)
        success_rate = (successful / total_checks) * 100

        print("=" * 60)
        print(f"Compatibility: {successful}/{total_checks} checks passed ({success_rate:.1f}%)")
        print("=" * 60)

        # Exit with success if core DSPy is installed
        # Other components are optional for experimental features
        sys.exit(0)
    else:
        print("=" * 60)
        print("DSPy not installed - this is acceptable for core functionality")
        print("DSPy agents are experimental and optional")
        print("=" * 60)
        # Exit with success - DSPy is optional
        sys.exit(0)


if __name__ == "__main__":
    main()
