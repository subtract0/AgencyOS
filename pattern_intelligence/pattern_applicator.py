"""
PatternApplicator - Automatic pattern recognition and application.

The core intelligence engine that:
- Recognizes when current context matches stored patterns
- Retrieves relevant patterns using semantic search
- Automatically applies patterns through agent actions
- Tracks application success and updates pattern effectiveness
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from shared.type_definitions.json import JSONValue
from datetime import datetime
import json

from .pattern_store import PatternStore, PatternSearchResult
from .coding_pattern import CodingPattern, ProblemContext

logger = logging.getLogger(__name__)


class PatternApplicator:
    """
    Automatic pattern recognition and application engine.

    The intelligence core that makes coding patterns actionable by:
    1. Context Recognition - Detect when current situation matches stored patterns
    2. Pattern Retrieval - Find most relevant patterns using semantic search
    3. Application Engine - Execute pattern recommendations
    4. Feedback Loop - Track success and update pattern effectiveness
    """

    def __init__(self, pattern_store: PatternStore, confidence_threshold: float = 0.7):
        """
        Initialize pattern applicator.

        Args:
            pattern_store: PatternStore instance for pattern retrieval
            confidence_threshold: Minimum confidence for pattern application
        """
        self.pattern_store = pattern_store
        self.confidence_threshold = confidence_threshold
        self.application_history: List[Dict[str, JSONValue]] = []

        logger.info(f"PatternApplicator initialized with confidence threshold: {confidence_threshold}")

    def analyze_context(
        self,
        description: str,
        domain: str = None,
        constraints: List[str] = None,
        symptoms: List[str] = None,
        current_tools: List[str] = None
    ) -> List[PatternSearchResult]:
        """
        Analyze current context and find matching patterns.

        Args:
            description: Description of current problem/task
            domain: Problem domain (e.g., "error_handling", "architecture")
            constraints: Current constraints
            symptoms: Observable symptoms
            current_tools: Tools currently available

        Returns:
            List of relevant patterns with relevance scores
        """
        try:
            # Create problem context for search
            context = ProblemContext(
                description=description,
                domain=domain or "general",
                constraints=constraints or [],
                symptoms=symptoms or []
            )

            # Search for relevant patterns
            search_results = self.pattern_store.find_patterns(
                context=context,
                domain=domain,
                min_effectiveness=0.5,
                max_results=10
            )

            # Filter by relevance and applicability
            applicable_patterns = []
            for result in search_results:
                if self._is_pattern_applicable(result.pattern, context, current_tools):
                    applicable_patterns.append(result)

            # Sort by combined relevance and effectiveness
            applicable_patterns.sort(
                key=lambda r: r.relevance_score * r.pattern.outcome.effectiveness_score(),
                reverse=True
            )

            logger.info(f"Found {len(applicable_patterns)} applicable patterns for context: {description[:50]}...")
            return applicable_patterns

        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return []

    def get_pattern_recommendations(
        self,
        context_description: str,
        domain: str = None,
        max_recommendations: int = 3
    ) -> List[Dict[str, JSONValue]]:
        """
        Get actionable pattern recommendations for current context.

        Args:
            context_description: Description of current situation
            domain: Problem domain
            max_recommendations: Maximum number of recommendations

        Returns:
            List of pattern recommendations with application instructions
        """
        try:
            # Find applicable patterns
            pattern_results = self.analyze_context(context_description, domain)

            if not pattern_results:
                return [{
                    "message": "No relevant patterns found",
                    "suggestion": "This might be a novel situation. Consider documenting the approach for future use.",
                    "confidence": 0.0
                }]

            recommendations = []

            for result in pattern_results[:max_recommendations]:
                pattern = result.pattern

                # Generate recommendation
                recommendation = {
                    "pattern_id": pattern.metadata.pattern_id,
                    "title": f"Apply {pattern.context.domain} pattern",
                    "description": pattern.context.description,
                    "approach": pattern.solution.approach,
                    "implementation": pattern.solution.implementation,
                    "tools_needed": pattern.solution.tools,
                    "expected_outcome": pattern.outcome.effectiveness_score(),
                    "success_rate": pattern.outcome.success_rate,
                    "confidence": result.relevance_score,
                    "application_instructions": pattern.get_application_instructions(),
                    "reasoning": f"Pattern matches current context ({result.match_reason}) with {result.relevance_score:.1%} relevance",
                    "dependencies": pattern.solution.dependencies,
                    "code_examples": pattern.solution.code_examples,
                    "alternatives": pattern.solution.alternatives
                }

                # Add warning if pattern has low effectiveness
                if pattern.outcome.effectiveness_score() < 0.6:
                    recommendation["warning"] = "This pattern has moderate effectiveness. Consider careful evaluation."

                # Add boost if pattern has high adoption
                if pattern.outcome.adoption_rate >= 5:
                    recommendation["boost"] = f"Widely adopted pattern ({pattern.outcome.adoption_rate} uses)"

                recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate pattern recommendations: {e}")
            return [{"error": f"Recommendation generation failed: {str(e)}"}]

    def auto_apply_pattern(
        self,
        pattern_id: str,
        context_data: Dict[str, JSONValue],
        dry_run: bool = True
    ) -> Dict[str, JSONValue]:
        """
        Automatically apply a pattern (or simulate if dry_run=True).

        Args:
            pattern_id: ID of pattern to apply
            context_data: Current context information
            dry_run: If True, simulate application without making changes

        Returns:
            Application result with success status and details
        """
        try:
            # Get the pattern
            pattern = self.pattern_store.get_pattern(pattern_id)
            if not pattern:
                return {"success": False, "error": f"Pattern {pattern_id} not found"}

            # Validate pattern can be applied
            validation_result = self._validate_pattern_application(pattern, context_data)
            if not validation_result["can_apply"]:
                return {
                    "success": False,
                    "error": f"Pattern cannot be applied: {validation_result['reason']}",
                    "pattern_id": pattern_id
                }

            # Generate application plan
            application_plan = self._generate_application_plan(pattern, context_data)

            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "pattern_id": pattern_id,
                    "application_plan": application_plan,
                    "estimated_success_rate": pattern.outcome.success_rate,
                    "tools_required": pattern.solution.tools,
                    "steps": application_plan.get("steps", [])
                }

            # Actually apply the pattern
            application_result = self._execute_application_plan(application_plan, pattern)

            # Record application attempt
            self._record_application(pattern_id, context_data, application_result)

            # Update pattern usage statistics
            self.pattern_store.update_pattern_usage(
                pattern_id,
                success=application_result.get("success", False)
            )

            return application_result

        except Exception as e:
            logger.error(f"Pattern application failed: {e}")
            return {
                "success": False,
                "error": f"Application failed: {str(e)}",
                "pattern_id": pattern_id
            }

    def suggest_pattern_combinations(
        self,
        context_description: str,
        domain: str = None
    ) -> List[Dict[str, JSONValue]]:
        """
        Suggest combinations of patterns that work well together.

        Args:
            context_description: Description of current situation
            domain: Problem domain

        Returns:
            List of pattern combination suggestions
        """
        try:
            # Get individual patterns
            individual_patterns = self.analyze_context(context_description, domain)

            if len(individual_patterns) < 2:
                return []

            combinations = []

            # Look for complementary patterns
            for i, pattern1 in enumerate(individual_patterns[:3]):
                for pattern2 in individual_patterns[i+1:4]:
                    if self._are_patterns_complementary(pattern1.pattern, pattern2.pattern):
                        combination = {
                            "patterns": [pattern1.pattern.metadata.pattern_id, pattern2.pattern.metadata.pattern_id],
                            "description": f"Combine {pattern1.pattern.context.domain} and {pattern2.pattern.context.domain} approaches",
                            "synergy_score": self._calculate_synergy_score(pattern1.pattern, pattern2.pattern),
                            "combined_effectiveness": (pattern1.pattern.outcome.effectiveness_score() +
                                                    pattern2.pattern.outcome.effectiveness_score()) / 2,
                            "application_order": self._determine_application_order(pattern1.pattern, pattern2.pattern),
                            "reasoning": f"These patterns address complementary aspects of the problem"
                        }

                        if combination["synergy_score"] > 0.6:
                            combinations.append(combination)

            # Sort by synergy score
            combinations.sort(key=lambda c: c["synergy_score"], reverse=True)

            return combinations[:3]  # Return top 3 combinations

        except Exception as e:
            logger.error(f"Pattern combination suggestion failed: {e}")
            return []

    def get_application_stats(self) -> Dict[str, JSONValue]:
        """Get statistics about pattern applications."""
        if not self.application_history:
            return {"total_applications": 0, "message": "No applications recorded yet"}

        total_applications = len(self.application_history)
        successful_applications = len([a for a in self.application_history if a.get("success", False)])

        success_rate = successful_applications / total_applications

        # Most applied patterns
        pattern_counts = {}
        for app in self.application_history:
            pattern_id = app.get("pattern_id")
            if pattern_id:
                pattern_counts[pattern_id] = pattern_counts.get(pattern_id, 0) + 1

        most_applied = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_applications": total_applications,
            "successful_applications": successful_applications,
            "success_rate": success_rate,
            "most_applied_patterns": most_applied,
            "confidence_threshold": self.confidence_threshold,
            "last_updated": datetime.now().isoformat()
        }

    def _is_pattern_applicable(
        self,
        pattern: CodingPattern,
        context: ProblemContext,
        available_tools: List[str] = None
    ) -> bool:
        """Check if a pattern can be applied in the current context."""
        try:
            # Check if pattern is validated and not deprecated
            if pattern.metadata.validation_status == "deprecated":
                return False

            # Check minimum effectiveness threshold
            if pattern.outcome.effectiveness_score() < 0.4:
                return False

            # Check if required tools are available
            if available_tools and pattern.solution.tools:
                required_tools = set(pattern.solution.tools)
                available_tools_set = set(available_tools)

                # Must have at least 50% of required tools
                if len(required_tools.intersection(available_tools_set)) < len(required_tools) * 0.5:
                    return False

            # Check domain compatibility
            if context.domain != "general" and pattern.context.domain != "general":
                if context.domain != pattern.context.domain:
                    # Allow cross-domain if high effectiveness
                    if pattern.outcome.effectiveness_score() < 0.8:
                        return False

            return True

        except Exception as e:
            logger.debug(f"Pattern applicability check failed: {e}")
            return False

    def _validate_pattern_application(
        self,
        pattern: CodingPattern,
        context_data: Dict[str, JSONValue]
    ) -> Dict[str, JSONValue]:
        """Validate that a pattern can be safely applied."""
        validation = {"can_apply": True, "reason": ""}

        try:
            # Check pattern status
            if pattern.metadata.validation_status == "deprecated":
                return {"can_apply": False, "reason": "Pattern is deprecated"}

            # Check effectiveness threshold
            if pattern.outcome.effectiveness_score() < 0.3:
                return {"can_apply": False, "reason": "Pattern effectiveness too low"}

            # Check dependencies
            if pattern.solution.dependencies:
                for dependency in pattern.solution.dependencies:
                    # In a real implementation, this would check if dependencies are available
                    # For now, we'll assume they are
                    pass

            # Check constraints compatibility
            current_constraints = context_data.get("constraints", [])
            pattern_constraints = pattern.context.constraints

            # Look for conflicting constraints
            conflicts = self._find_constraint_conflicts(current_constraints, pattern_constraints)
            if conflicts:
                return {"can_apply": False, "reason": f"Constraint conflicts: {', '.join(conflicts)}"}

            return validation

        except Exception as e:
            return {"can_apply": False, "reason": f"Validation failed: {str(e)}"}

    def _generate_application_plan(
        self,
        pattern: CodingPattern,
        context_data: Dict[str, JSONValue]
    ) -> Dict[str, JSONValue]:
        """Generate a detailed plan for applying the pattern."""
        plan = {
            "pattern_id": pattern.metadata.pattern_id,
            "approach": pattern.solution.approach,
            "steps": [],
            "tools_needed": pattern.solution.tools,
            "dependencies": pattern.solution.dependencies,
            "expected_outcome": pattern.outcome.effectiveness_score(),
            "risks": [],
            "validation_criteria": []
        }

        try:
            # Generate implementation steps
            if pattern.solution.implementation:
                steps = pattern.solution.implementation.split(',')
                plan["steps"] = [step.strip() for step in steps if step.strip()]

            # Add tool-specific steps
            for tool in pattern.solution.tools:
                plan["steps"].append(f"Prepare and configure {tool}")

            # Add validation steps
            plan["validation_criteria"] = [
                "Verify implementation matches pattern requirements",
                "Test functionality and performance",
                "Validate against success metrics"
            ]

            # Identify risks
            if pattern.outcome.success_rate < 0.8:
                plan["risks"].append(f"Pattern has {pattern.outcome.success_rate:.1%} success rate")

            if pattern.solution.dependencies:
                plan["risks"].append("Depends on external dependencies")

            return plan

        except Exception as e:
            logger.error(f"Application plan generation failed: {e}")
            plan["error"] = str(e)
            return plan

    def _execute_application_plan(
        self,
        plan: Dict[str, JSONValue],
        pattern: CodingPattern
    ) -> Dict[str, JSONValue]:
        """Execute the application plan (simulation for now)."""
        # In a real implementation, this would:
        # 1. Execute the actual steps
        # 2. Use the required tools
        # 3. Apply the pattern's solution
        # 4. Validate the results

        # For now, we'll simulate the execution
        result = {
            "success": True,
            "pattern_id": pattern.metadata.pattern_id,
            "execution_time": datetime.now().isoformat(),
            "steps_completed": len(plan.get("steps", [])),
            "simulation": True,
            "message": "Pattern application simulated successfully"
        }

        # Simulate success based on pattern's historical success rate
        import random
        success_probability = pattern.outcome.success_rate
        simulated_success = random.random() < success_probability

        result["success"] = simulated_success

        if not simulated_success:
            result["message"] = "Pattern application failed (simulated)"
            result["error"] = "Simulated failure based on historical success rate"

        return result

    def _record_application(
        self,
        pattern_id: str,
        context_data: Dict[str, JSONValue],
        result: Dict[str, JSONValue]
    ) -> None:
        """Record a pattern application attempt."""
        application_record = {
            "pattern_id": pattern_id,
            "timestamp": datetime.now().isoformat(),
            "context": context_data,
            "result": result,
            "success": result.get("success", False)
        }

        self.application_history.append(application_record)

        # Keep only last 100 applications
        if len(self.application_history) > 100:
            self.application_history = self.application_history[-100:]

    def _are_patterns_complementary(
        self,
        pattern1: CodingPattern,
        pattern2: CodingPattern
    ) -> bool:
        """Check if two patterns are complementary and can work together."""
        try:
            # Different domains often complement each other
            if pattern1.context.domain != pattern2.context.domain:
                return True

            # Different tools suggest complementary approaches
            tools1 = set(pattern1.solution.tools)
            tools2 = set(pattern2.solution.tools)

            if tools1 and tools2 and not tools1.intersection(tools2):
                return True

            # Different constraint handling
            constraints1 = set(pattern1.context.constraints)
            constraints2 = set(pattern2.context.constraints)

            if constraints1 and constraints2 and not constraints1.intersection(constraints2):
                return True

            return False

        except Exception:
            return False

    def _calculate_synergy_score(
        self,
        pattern1: CodingPattern,
        pattern2: CodingPattern
    ) -> float:
        """Calculate synergy score for pattern combination."""
        try:
            score = 0.0

            # Base score from individual effectiveness
            score += (pattern1.outcome.effectiveness_score() + pattern2.outcome.effectiveness_score()) / 2 * 0.4

            # Bonus for complementary domains
            if pattern1.context.domain != pattern2.context.domain:
                score += 0.2

            # Bonus for non-overlapping tools
            tools1 = set(pattern1.solution.tools)
            tools2 = set(pattern2.solution.tools)
            if tools1 and tools2 and not tools1.intersection(tools2):
                score += 0.2

            # Bonus for high success rates
            if pattern1.outcome.success_rate > 0.8 and pattern2.outcome.success_rate > 0.8:
                score += 0.2

            return min(1.0, score)

        except Exception:
            return 0.0

    def _determine_application_order(
        self,
        pattern1: CodingPattern,
        pattern2: CodingPattern
    ) -> List[str]:
        """Determine optimal order for applying patterns."""
        # Simple heuristic: apply architectural patterns first, then implementation patterns
        architectural_domains = ["architecture", "design", "structure"]
        implementation_domains = ["implementation", "coding", "testing"]

        if pattern1.context.domain in architectural_domains:
            return [pattern1.metadata.pattern_id, pattern2.metadata.pattern_id]
        elif pattern2.context.domain in architectural_domains:
            return [pattern2.metadata.pattern_id, pattern1.metadata.pattern_id]
        else:
            # Order by effectiveness score
            if pattern1.outcome.effectiveness_score() >= pattern2.outcome.effectiveness_score():
                return [pattern1.metadata.pattern_id, pattern2.metadata.pattern_id]
            else:
                return [pattern2.metadata.pattern_id, pattern1.metadata.pattern_id]

    def _find_constraint_conflicts(
        self,
        current_constraints: List[str],
        pattern_constraints: List[str]
    ) -> List[str]:
        """Find conflicts between current and pattern constraints."""
        conflicts = []

        # Define known conflicting constraint pairs
        conflict_pairs = [
            ("fast", "comprehensive"),
            ("simple", "feature_rich"),
            ("secure", "convenient"),
            ("lightweight", "full_featured")
        ]

        current_set = set(c.lower() for c in current_constraints)
        pattern_set = set(c.lower() for c in pattern_constraints)

        for curr_constraint in current_set:
            for pattern_constraint in pattern_set:
                for pair in conflict_pairs:
                    if (curr_constraint in pair[0] and pattern_constraint in pair[1]) or \
                       (curr_constraint in pair[1] and pattern_constraint in pair[0]):
                        conflicts.append(f"{curr_constraint} vs {pattern_constraint}")

        return conflicts