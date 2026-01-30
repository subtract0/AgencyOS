
import logging
from typing import Optional
from cells.maintenance.medic_agent import create_medic_agent
from cells.maintenance.refactor_agent import RefactorAgent
from cells.shared.lean_agent import LeanAgent, tool, ToolParameter

logger = logging.getLogger(__name__)

class MaintenanceSupervisor:
    """
    The Golden Loop Supervisor.
    Orchestrates the Immune System (Medic) and Evolution System (Refactor).
    """
    
    def __init__(self):
        self.medic = create_medic_agent(model="gpt-4o") # Strong model for debugging
        self.refactor = RefactorAgent()
        
    def run_cycle(self) -> str:
        """
        Run one maintenance cycle.
        1. Connectivity/Health Check (Medic)
        2. Evolution Step (Refactor) - Only if Healthy
        """
        report = []
        report.append("🔄 Maintenance Cycle Started.")
        
        # --- Phase 1: The Medic ---
        report.append("🚑 Phase 1: Medic Check...")
        try:
            # We ask Medic to verify health.
            medic_response = self.medic.run(
                "Run the full test suite (fast mode). "
                "If tests fail, fix them. "
                "If tests pass, simply reply with 'SYSTEM GREEN'."
            )
            report.append(f"Medic: {medic_response}")
            
            if "SYSTEM GREEN" not in medic_response and "Tests Passed" not in medic_response:
                return "\n".join(report + ["🛑 Cycle Halting: System Unhealthy."])
                
        except Exception as e:
            return "\n".join(report + [f"❌ Medic CRITICAL FAILURE: {e}"])

        # --- Phase 2: The Refactor ---
        report.append("🏗️ Phase 2: Refactor (Evolution)...")
        try:
            # We ask Refactor to do one small thing
            refactor_response = self.refactor.run(
                "Scan the codebase for ONE high-value, low-risk improvement (e.g. unused import, 'loose' file, typo). "
                "Explain the issue, then fix it. "
                "Do not attempt risky architectural changes."
            )
            report.append(f"Refactor: {refactor_response}")
        except Exception as e:
            report.append(f"⚠️ Refactor Error: {e} (Non-fatal)")

        report.append("✅ Cycle Complete.")
        return "\n".join(report)

@tool(
    name="run_maintenance_cycle", 
    description="Manually trigger the Maintenance Supervisor (Medic + Refactor loop).",
    parameters=ToolParameter(type="object", properties={}, required=[])
)
def run_maintenance_cycle_tool() -> str:
    supervisor = MaintenanceSupervisor()
    return supervisor.run_cycle()

if __name__ == "__main__":
    # Standalone run
    print(run_maintenance_cycle_tool())
