import os
import json
from datetime import datetime
from typing import Any, Dict
from shared.type_definitions.json import JSONValue

from agency_swarm.tools import BaseTool
from pydantic import Field

from auditor_agent.ast_analyzer import ASTAnalyzer
from agency_memory import VectorStore


class RunArchitectureLoop(BaseTool):
    target_path: str = Field(default=os.getcwd(), description="Root of the repository to audit")
    objective: str = Field(default="auto", description="Optional explicit objective override")

    def run(self) -> str:
        findings: Dict[str, JSONValue] = {"timestamp": datetime.now().isoformat()}

        analyzer = ASTAnalyzer()
        analysis = analyzer.analyze_directory(self.target_path)
        findings["audit"] = {
            "total_behaviors": analysis.get("total_behaviors", 0),
            "total_tests": analysis.get("total_test_functions", 0),
        }

        vs = VectorStore()
        stats = vs.get_stats()
        findings["vector_store_stats"] = stats

        api_mismatches = self._detect_vectorstore_api_mismatches()
        findings["api_mismatches"] = api_mismatches

        target = self._choose_high_impact_target(findings)
        findings["selected_target"] = target

        out_path = os.path.join("logs", "chief_architect_findings.json")
        try:
            os.makedirs("logs", exist_ok=True)
            with open(out_path, "w") as f:
                json.dump(findings, f, indent=2)
        except Exception:
            pass

        return json.dumps(findings, indent=2)

    def _detect_vectorstore_api_mismatches(self) -> Dict[str, JSONValue]:
        mismatches: Dict[str, JSONValue] = {"issues": []}
        try:
            import inspect
            import agency_memory.vector_store as vs_mod

            methods = {name for name, _ in inspect.getmembers(vs_mod.VectorStore, inspect.isfunction)}

            if "search" not in methods:
                mismatches["issues"].append("VectorStore missing .search API used by LearningAgent")

            try:
                from learning_agent.tools.store_knowledge import StoreKnowledge  # noqa: F401
                uses_search = True
            except Exception:
                uses_search = False

            mismatches["learning_uses_search"] = uses_search
        except Exception as e:
            mismatches["error"] = str(e)
        return mismatches

    def _choose_high_impact_target(self, findings: Dict[str, JSONValue]) -> Dict[str, str]:
        issues = findings.get("api_mismatches", {}).get("issues", [])
        if any("VectorStore" in i for i in issues):
            return {
                "title": "Harmonize VectorStore API with LearningAgent",
                "reason": "Unblocks continuous learning pipeline and prevents recurring integration errors",
            }
        return {"title": "Improve test coverage", "reason": "Default fallback"}
