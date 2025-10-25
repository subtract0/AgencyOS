#!/usr/bin/env python3
"""
Esper3.1 + TRM Integration
Routes tasks between gpt-oss-20b-Esper3.1 and TRM based on complexity.

Architecture:
    gpt-oss-20b-Esper3.1 (Router + Generalist + Translator)
        ├─ Simple tasks (use_trm=0) → Esper3.1 handles solo
        └─ Complex tasks (use_trm=1) → Esper3.1 translates → TRM executes

Usage:
    from tools.esper31_trm_executor import Esper31TRMExecutor

    executor = Esper31TRMExecutor()
    result = executor.execute("Find shortest path from A to C in graph...")
"""
import json
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path

# Import TRM executor
from tools.trm_executor import TRMExecutor


class Esper31TRMExecutor:
    """
    Main executor integrating Esper3.1 (Ollama) with TRM.
    """

    def __init__(
        self,
        esper31_model: str = "gpt-oss:20b",  # Ollama model name
        trm_checkpoint: str = "models/trm-checkpoints/arc_v1_public/step_518071",
        use_trm: bool = True,  # Enable/disable TRM delegation
    ):
        """
        Initialize Esper3.1 + TRM executor.

        Args:
            esper31_model: Ollama model name for Esper3.1
            trm_checkpoint: Path to TRM checkpoint
            use_trm: Enable TRM delegation
        """
        self.esper31_model = esper31_model
        self.use_trm = use_trm

        # Initialize TRM (if enabled)
        if self.use_trm:
            try:
                self.trm_executor = TRMExecutor(checkpoint_path=trm_checkpoint)
                print(f"✅ TRM executor initialized")
            except Exception as e:
                print(f"⚠️  TRM initialization failed: {e}")
                print(f"   Falling back to Esper3.1-only mode")
                self.use_trm = False

        print(f"✅ Esper31TRMExecutor ready")
        print(f"   Esper3.1 model: {self.esper31_model}")
        print(f"   TRM enabled: {self.use_trm}")

    def execute(
        self,
        instruction: str,
        input_data: str = "",
        reasoning_level: str = "high"
    ) -> Dict[str, Any]:
        """
        Execute task with Esper3.1 + TRM routing.

        Args:
            instruction: Task description
            input_data: Optional input data
            reasoning_level: Esper3.1 reasoning level (low, medium, high)

        Returns:
            {
                "executor": "esper31" | "trm" | "esper31_fallback",
                "output": <solution>,
                "reasoning": <optional reasoning trace>,
                "metadata": <execution metadata>
            }
        """
        # Step 1: Ask Esper3.1 to decide + translate
        decision = self._get_routing_decision(instruction, input_data, reasoning_level)

        # Step 2: Route based on decision
        if decision["action"] == "solo" or not self.use_trm:
            # Esper3.1 handles directly
            return {
                "executor": "esper31",
                "output": decision.get("output", ""),
                "reasoning": decision.get("reasoning", ""),
                "metadata": {
                    "model": self.esper31_model,
                    "reasoning_level": reasoning_level
                }
            }

        elif decision["action"] == "delegate_trm":
            # Delegate to TRM
            trm_task = decision.get("trm_task", {})

            print(f"🔄 Delegating to TRM...")
            print(f"   Task type: {trm_task.get('task_type', 'N/A')}")

            trm_result = self.trm_executor.execute(trm_task)

            if trm_result["success"]:
                return {
                    "executor": "trm",
                    "output": trm_result["output"],
                    "reasoning": f"TRM solved in {trm_result['iterations_used']} iterations",
                    "metadata": {
                        "model": "TRM-7M",
                        "iterations": trm_result["iterations_used"],
                        "confidence": trm_result["confidence"]
                    }
                }
            else:
                # TRM failed, fallback to Esper3.1
                print(f"⚠️  TRM failed: {trm_result['error']}")
                print(f"   Falling back to Esper3.1...")
                return self._execute_solo_fallback(instruction, input_data, reasoning_level)

        else:
            raise ValueError(f"Unknown action: {decision.get('action')}")

    def _get_routing_decision(
        self,
        instruction: str,
        input_data: str,
        reasoning_level: str
    ) -> Dict[str, Any]:
        """
        Ask Esper3.1 to decide routing and translate task if needed.

        Prompt format:
            System: You are Esper3.1 with TRM delegation capability.
            User: <instruction> + <input>
            Expected response:
            {
                "action": "solo" | "delegate_trm",
                "output": "<if solo>",
                "reasoning": "<explanation>",
                "trm_task": {<if delegate_trm>}
            }

        Returns:
            Decision dict
        """
        system_prompt = """You are Esper3.1, a coding, architecture, and DevOps specialist with TRM (Tiny Recursive Model) delegation capability.

Decide if this task should be:
1. Handled SOLO (action: "solo"): Straightforward coding, DevOps, architecture tasks
2. Delegated to TRM (action: "delegate_trm"): Complex graph/optimization/recursive reasoning tasks

If delegating to TRM, translate the task to this format:
{
  "task_type": "GRAPH|CSP|OPTIMIZATION|RECURSION|ARC_AGI",
  "input": "<canonical format - e.g. nodes:[A,B,C];edges:[A-B:3]>",
  "max_iterations": <1-16>,
  "expected_output_schema": "<JSON schema>"
}

Respond ONLY in JSON format."""

        user_prompt = f"""Task:
Instruction: {instruction}
Input: {input_data}

Respond in JSON:
{{
  "action": "solo" or "delegate_trm",
  "output": "<your solution if solo>",
  "reasoning": "<why you chose this action>",
  "trm_task": {{<TRM task spec if delegating>}} or null
}}"""

        # Call Esper3.1 via Ollama
        try:
            result = subprocess.run(
                [
                    "ollama", "run", self.esper31_model,
                    f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n"
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise RuntimeError(f"Ollama error: {result.stderr}")

            # Parse JSON response
            response_text = result.stdout.strip()

            # Extract JSON from response (may have markdown fences)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            decision = json.loads(response_text)
            return decision

        except Exception as e:
            print(f"⚠️  Esper3.1 routing failed: {e}")
            print(f"   Defaulting to solo execution...")
            return {
                "action": "solo",
                "output": f"Error in routing: {e}. Executing solo.",
                "reasoning": f"Routing error: {e}"
            }

    def _execute_solo_fallback(
        self,
        instruction: str,
        input_data: str,
        reasoning_level: str
    ) -> Dict[str, Any]:
        """
        Fallback to Esper3.1 solo execution when TRM fails.
        """
        prompt = f"""<|system|>
You are Esper3.1, a coding and architecture specialist. Solve this task directly (TRM unavailable).
<|user|>
{instruction}
Input: {input_data}
<|assistant|>
"""

        result = subprocess.run(
            [
                "ollama", "run", self.esper31_model,
                "--",
                prompt
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        return {
            "executor": "esper31_fallback",
            "output": result.stdout.strip(),
            "reasoning": "TRM failed, Esper3.1 fallback",
            "metadata": {
                "model": self.esper31_model,
                "reasoning_level": reasoning_level
            }
        }


def main():
    """Test Esper3.1 + TRM integration."""
    print("=" * 70)
    print("ESPER3.1 + TRM INTEGRATION TEST")
    print("=" * 70)

    # Initialize executor
    executor = Esper31TRMExecutor()

    # Test cases
    test_cases = [
        {
            "name": "Simple Coding Task",
            "instruction": "Write a Python function that reads a JSON file and returns its contents",
            "input": "File path: data/config.json",
            "expected_executor": "esper31"
        },
        {
            "name": "Graph Shortest Path (TRM)",
            "instruction": "Find the shortest path from node A to node C",
            "input": "Graph: nodes A,B,C; edges A-B:3, B-C:2, A-C:8",
            "expected_executor": "trm"
        },
        {
            "name": "DevOps Task",
            "instruction": "Write a bash script to check if a service is running and restart it if not",
            "input": "Service name: nginx",
            "expected_executor": "esper31"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'=' * 70}")
        print(f"Instruction: {test['instruction']}")
        print(f"Input: {test['input']}")
        print(f"Expected executor: {test['expected_executor']}")

        print(f"\n🚀 Executing...")
        result = executor.execute(
            instruction=test['instruction'],
            input_data=test['input']
        )

        print(f"\n📊 Result:")
        print(f"   Executor: {result['executor']}")
        print(f"   Reasoning: {result['reasoning']}")
        print(f"   Output: {result['output'][:200]}...")
        print(f"   Metadata: {json.dumps(result['metadata'], indent=2)}")

        if result['executor'] == test['expected_executor']:
            print(f"   ✅ Correct routing!")
        else:
            print(f"   ⚠️  Unexpected routing (expected {test['expected_executor']})")

    print(f"\n{'=' * 70}")
    print("TEST COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
