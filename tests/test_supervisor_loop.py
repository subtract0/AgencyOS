
import pytest
from cells.maintenance.supervisor import MaintenanceSupervisor

def test_supervisor_cycle_structure():
    """
    Smoke test for Supervisor Cycle.
    We don't want to actually wait for GPT-4 to run tests in CI ideally,
    but for this env it is fine.
    
    To be safe/fast, we can mock the agents or just run them if we trust the environment.
    Let's run them but expect a string output.
    """
    supervisor = MaintenanceSupervisor()
    
    # We can inspect the components exist
    assert supervisor.medic is not None
    assert supervisor.refactor is not None
    
    # To avoid long blocking calls in a simple test, we might mock run.
    # But "The Proof is in the Pudding" - Agent Zero philosophy says RUN IT.
    
    # However, running the full cycle involves:
    # 1. Medic running tests (takes ~5s)
    # 2. Refactor scanning (takes ~5s)
    # Total ~10-20s. Acceptable.
    
    # Note: This requires active LLM credentials.
    try:
        result = supervisor.run_cycle()
        print(f"\nSupervisor Output:\n{result}\n")
        assert "Maintenance Cycle Started" in result
        assert "Medic" in result
    except Exception as e:
        pytest.fail(f"Supervisor crashed: {e}")

if __name__ == "__main__":
    test_supervisor_cycle_structure()
