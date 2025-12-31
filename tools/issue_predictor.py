"""
Issue Predictor - ML-based code quality issue prediction.

Uses historical patterns and naive Bayes classification to predict
which code patterns are likely to cause issues.

Constitutional Compliance:
- Article III: Automated enforcement (predictive prevention)
- Article IV: Learning integration (learns from outcomes)
"""

import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


MODEL_PATH = PROJECT_ROOT / "logs" / "issue_predictor_model.json"


@dataclass
class Prediction:
    """A predicted issue classification."""

    code_snippet: str
    predicted_issue: str
    probability: float
    confidence: str  # 'high', 'medium', 'low'
    similar_patterns: list[str]


@dataclass
class ModelStats:
    """Statistics about the prediction model."""

    total_samples: int
    issue_types: list[str]
    accuracy: float
    last_trained: str
    feature_importance: dict[str, float]


class IssuePredictorModel:
    """
    Naive Bayes classifier for code issue prediction.

    Uses word/token frequencies to classify code snippets
    into issue categories or 'clean'.
    """

    def __init__(self):
        """Initialize the predictor model."""
        # Class priors P(class)
        self.class_counts: Counter = Counter()
        self.total_samples: int = 0

        # Feature likelihood P(feature|class)
        self.feature_counts: dict[str, Counter] = defaultdict(Counter)
        self.feature_totals: dict[str, int] = defaultdict(int)

        # Vocabulary
        self.vocabulary: set[str] = set()

        # Training history
        self.training_history: list[dict] = []

        # Load model if exists
        self._load_model()

    def _load_model(self) -> None:
        """Load model from disk if available."""
        if MODEL_PATH.exists():
            try:
                data = json.loads(MODEL_PATH.read_text())
                self.class_counts = Counter(data.get("class_counts", {}))
                self.total_samples = data.get("total_samples", 0)
                self.feature_counts = {
                    k: Counter(v) for k, v in data.get("feature_counts", {}).items()
                }
                self.feature_totals = dict(data.get("feature_totals", {}))
                self.vocabulary = set(data.get("vocabulary", []))
                self.training_history = data.get("training_history", [])
            except Exception:
                pass

    def _save_model(self) -> None:
        """Save model to disk."""
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "class_counts": dict(self.class_counts),
            "total_samples": self.total_samples,
            "feature_counts": {k: dict(v) for k, v in self.feature_counts.items()},
            "feature_totals": dict(self.feature_totals),
            "vocabulary": list(self.vocabulary),
            "training_history": self.training_history[-100:],  # Keep last 100
        }

        MODEL_PATH.write_text(json.dumps(data, indent=2))

    def _tokenize(self, code: str) -> list[str]:
        """Tokenize code into features."""
        import re

        # Normalize
        code = code.lower()

        # Extract tokens
        tokens = []

        # Python keywords and operators
        keywords = re.findall(
            r"\b(def|class|if|else|elif|for|while|try|except|finally|with|"
            r"import|from|return|yield|raise|pass|break|continue|"
            r"and|or|not|in|is|lambda|global|nonlocal|assert|async|await)\b",
            code,
        )
        tokens.extend(keywords)

        # Type hints
        type_patterns = re.findall(
            r"\b(Dict|List|Set|Tuple|Optional|Any|Union|Type|Callable)\b",
            code,
            re.IGNORECASE,
        )
        tokens.extend([f"type_{t.lower()}" for t in type_patterns])

        # Exception handling patterns
        if "except:" in code:
            tokens.append("bare_except")
        if "except Exception" in code:
            tokens.append("generic_exception")

        # Security-sensitive patterns
        if re.search(r"\beval\s*\(", code):
            tokens.append("uses_eval")
        if re.search(r"\bexec\s*\(", code):
            tokens.append("uses_exec")
        if re.search(r"shell\s*=\s*true", code):
            tokens.append("shell_true")

        # Code style patterns
        if re.search(r"^\s*print\s*\(", code, re.MULTILINE):
            tokens.append("has_print")
        if re.search(r"#\s*(TODO|FIXME|XXX)", code):
            tokens.append("has_todo")

        # Function patterns
        func_defs = re.findall(r"def\s+(\w+)\s*\(", code)
        for func in func_defs:
            if len(func) > 20:
                tokens.append("long_func_name")
            if func.startswith("_"):
                tokens.append("private_func")

        # Line count approximation
        line_count = code.count("\n") + 1
        if line_count > 50:
            tokens.append("long_code")
        elif line_count > 20:
            tokens.append("medium_code")
        else:
            tokens.append("short_code")

        # Indentation depth
        max_indent = max(
            (len(line) - len(line.lstrip()))
            for line in code.split("\n")
            if line.strip()
        )
        if max_indent > 16:
            tokens.append("deep_nesting")

        return tokens

    def train(self, code: str, issue_type: str) -> None:
        """
        Train the model on a labeled sample.

        Args:
            code: Code snippet
            issue_type: Issue type label ('clean' for no issues)
        """
        tokens = self._tokenize(code)

        # Update class counts
        self.class_counts[issue_type] += 1
        self.total_samples += 1

        # Update feature counts
        for token in tokens:
            self.feature_counts[issue_type][token] += 1
            self.feature_totals[issue_type] += 1
            self.vocabulary.add(token)

        # Record training
        self.training_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "issue_type": issue_type,
                "tokens": len(tokens),
            }
        )

        # Save periodically
        if self.total_samples % 10 == 0:
            self._save_model()

    def train_batch(self, samples: list[tuple[str, str]]) -> int:
        """
        Train on multiple samples.

        Args:
            samples: List of (code, issue_type) tuples

        Returns:
            Number of samples trained
        """
        for code, issue_type in samples:
            self.train(code, issue_type)

        self._save_model()
        return len(samples)

    def predict(self, code: str) -> Result[Prediction, str]:
        """
        Predict the most likely issue type for code.

        Args:
            code: Code snippet to classify

        Returns:
            Result containing prediction
        """
        if self.total_samples < 5:
            return Err("Model needs at least 5 training samples")

        tokens = self._tokenize(code)

        # Calculate log probabilities for each class
        class_scores: dict[str, float] = {}

        for issue_type in self.class_counts:
            # Log prior
            log_prior = math.log(self.class_counts[issue_type] / self.total_samples)

            # Log likelihood
            log_likelihood = 0.0
            vocab_size = len(self.vocabulary)

            for token in tokens:
                # Laplace smoothing
                token_count = self.feature_counts[issue_type].get(token, 0)
                total = self.feature_totals[issue_type]

                # P(token|class) with smoothing
                prob = (token_count + 1) / (total + vocab_size)
                log_likelihood += math.log(prob)

            class_scores[issue_type] = log_prior + log_likelihood

        # Normalize to probabilities
        max_score = max(class_scores.values())
        exp_scores = {k: math.exp(v - max_score) for k, v in class_scores.items()}
        total_exp = sum(exp_scores.values())
        probabilities = {k: v / total_exp for k, v in exp_scores.items()}

        # Get best prediction
        best_class = max(probabilities, key=lambda k: probabilities[k])
        best_prob = probabilities[best_class]

        # Determine confidence
        if best_prob > 0.8:
            confidence = "high"
        elif best_prob > 0.5:
            confidence = "medium"
        else:
            confidence = "low"

        # Find similar patterns
        similar = self._find_similar_patterns(tokens, best_class)

        return Ok(
            Prediction(
                code_snippet=code[:200],
                predicted_issue=best_class,
                probability=best_prob,
                confidence=confidence,
                similar_patterns=similar,
            )
        )

    def _find_similar_patterns(self, tokens: list[str], issue_type: str) -> list[str]:
        """Find similar token patterns from training."""
        if issue_type not in self.feature_counts:
            return []

        # Get top features for this class
        feature_probs = []
        for token, count in self.feature_counts[issue_type].items():
            prob = count / self.feature_totals[issue_type]
            if token in tokens:
                feature_probs.append((token, prob))

        feature_probs.sort(key=lambda x: x[1], reverse=True)
        return [t for t, _ in feature_probs[:5]]

    def get_stats(self) -> ModelStats:
        """Get model statistics."""
        # Calculate simple accuracy from recent history
        recent = self.training_history[-50:]
        accuracy = 0.0  # Would need validation set for real accuracy

        # Feature importance (most predictive features)
        feature_importance = {}
        for issue_type, counts in self.feature_counts.items():
            if issue_type == "clean":
                continue
            for token, count in counts.most_common(5):
                key = f"{issue_type}:{token}"
                feature_importance[key] = count / (self.feature_totals[issue_type] or 1)

        return ModelStats(
            total_samples=self.total_samples,
            issue_types=list(self.class_counts.keys()),
            accuracy=accuracy,
            last_trained=self.training_history[-1]["timestamp"]
            if self.training_history
            else "never",
            feature_importance=dict(
                sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[
                    :10
                ]
            ),
        )


class IssuePredictor:
    """
    High-level issue predictor combining model with heuristics.

    Uses the ML model along with rule-based predictions for
    robust issue detection.
    """

    def __init__(self):
        """Initialize the issue predictor."""
        self.model = IssuePredictorModel()
        self._seed_initial_data()

    def _seed_initial_data(self) -> None:
        """Seed model with initial training data if empty."""
        if self.model.total_samples >= 20:
            return

        # Training samples: (code, issue_type)
        samples = [
            # Bare except samples
            ("try:\n    x = 1\nexcept:\n    pass", "bare_except"),
            ("try:\n    do_something()\nexcept:\n    log_error()", "bare_except"),
            ("try:\n    open(f)\nexcept:\n    return None", "bare_except"),
            # Dict[Any, Any] samples
            ("data: Dict[Any, Any] = {}", "dict_any_any"),
            ("def get_data() -> Dict[Any, Any]:", "dict_any_any"),
            ("result: Dict[Any, Any] = parse(x)", "dict_any_any"),
            # Security issues
            ("result = eval(user_input)", "security_eval"),
            ("exec(code_string)", "security_exec"),
            ("subprocess.call(cmd, shell=True)", "security_shell"),
            # Clean code samples
            ("def add(a: int, b: int) -> int:\n    return a + b", "clean"),
            ("try:\n    x = 1\nexcept ValueError as e:\n    handle(e)", "clean"),
            ("data: dict[str, int] = {}", "clean"),
            ("for item in items:\n    process(item)", "clean"),
            ("class User:\n    def __init__(self, name: str):\n        self.name = name", "clean"),
            # TODO comments
            ("# TODO: fix this later\ndef broken():\n    pass", "todo_comment"),
            ("# FIXME: hack\nx = 1", "todo_comment"),
            # Print statements
            ("print('debug')\nx = 1", "debug_print"),
            ("print(f'value: {x}')", "debug_print"),
            # Long functions (simulated)
            ("\n".join(["    line = x" for _ in range(60)]), "long_function"),
            # More clean samples
            ("import json\n\ndef load(path: str) -> dict:\n    return json.load(open(path))", "clean"),
            ("async def fetch(url: str) -> str:\n    async with session.get(url) as r:\n        return await r.text()", "clean"),
        ]

        self.model.train_batch(samples)

    def predict(self, code: str) -> Result[Prediction, str]:
        """
        Predict issues in code.

        Args:
            code: Code to analyze

        Returns:
            Result containing prediction
        """
        return self.model.predict(code)

    def predict_file(self, file_path: str) -> Result[list[Prediction], str]:
        """
        Predict issues in a file by analyzing chunks.

        Args:
            file_path: Path to file

        Returns:
            Result containing list of predictions
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return Err(f"File not found: {file_path}")

            content = path.read_text()

            # Split by function/class definitions
            import re

            chunks = re.split(r"(?=\n(?:def |class |async def ))", content)

            predictions = []
            for chunk in chunks:
                if len(chunk.strip()) < 10:
                    continue

                result = self.predict(chunk)
                if result.is_ok():
                    pred = result.unwrap()
                    if pred.predicted_issue != "clean" and pred.probability > 0.5:
                        predictions.append(pred)

            return Ok(predictions)

        except Exception as e:
            return Err(f"Error analyzing file: {e}")

    def learn_from_outcome(self, code: str, actual_issue: str) -> None:
        """
        Update model from actual outcome.

        Args:
            code: Code that was analyzed
            actual_issue: Actual issue type found (or 'clean')
        """
        self.model.train(code, actual_issue)

    def get_stats(self) -> dict:
        """Get predictor statistics."""
        model_stats = self.model.get_stats()
        return {
            "total_samples": model_stats.total_samples,
            "issue_types": model_stats.issue_types,
            "last_trained": model_stats.last_trained,
            "top_features": model_stats.feature_importance,
        }


def main():
    """Command-line interface for issue predictor."""
    import argparse

    parser = argparse.ArgumentParser(description="ML-based issue predictor")
    parser.add_argument("--predict", help="Code string to predict")
    parser.add_argument("--file", help="File to analyze")
    parser.add_argument("--train", help="Train with code (requires --label)")
    parser.add_argument("--label", help="Issue label for training")
    parser.add_argument("--stats", action="store_true", help="Show model statistics")
    args = parser.parse_args()

    predictor = IssuePredictor()

    if args.stats:
        stats = predictor.get_stats()
        print("\n📊 Issue Predictor Statistics")
        print("=" * 50)
        print(f"Total samples: {stats['total_samples']}")
        print(f"Issue types: {', '.join(stats['issue_types'])}")
        print(f"Last trained: {stats['last_trained']}")
        if stats["top_features"]:
            print("\nTop predictive features:")
            for feature, importance in list(stats["top_features"].items())[:5]:
                print(f"  {feature}: {importance:.3f}")

    elif args.train and args.label:
        predictor.learn_from_outcome(args.train, args.label)
        print(f"✅ Trained model with label: {args.label}")

    elif args.predict:
        result = predictor.predict(args.predict)
        if result.is_ok():
            pred = result.unwrap()
            print(f"\n🔮 Prediction: {pred.predicted_issue}")
            print(f"   Probability: {pred.probability:.1%}")
            print(f"   Confidence: {pred.confidence}")
            if pred.similar_patterns:
                print(f"   Key features: {', '.join(pred.similar_patterns)}")
        else:
            print(f"Error: {result.unwrap_err()}")

    elif args.file:
        result = predictor.predict_file(args.file)
        if result.is_ok():
            predictions = result.unwrap()
            if predictions:
                print(f"\nFound {len(predictions)} potential issues:")
                for pred in predictions:
                    print(f"  - {pred.predicted_issue} ({pred.probability:.1%})")
            else:
                print("✅ No issues predicted")
        else:
            print(f"Error: {result.unwrap_err()}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
