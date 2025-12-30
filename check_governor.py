
from shared.budget_manager import BudgetManager
from shared.model_router import ModelRouter
import shutil
import os

print("# Testing The Governor (Class 2)...")

# 1. Setup Clean State
if os.path.exists(".agency_active"):
    shutil.rmtree(".agency_active")
    
budget = BudgetManager(settings_dir=".agency_active")
router = ModelRouter(budget)

print(f"Initial Budget: ${budget.get_current_spend()} (Remaining: ${budget.get_remaining_budget()})")

# 2. Test Simple Routing (Should be Local)
print("\n--- Test 1: Low Complexity Task ---")
decision = router.route(task_complexity="low")
print(f"Decision: {decision['provider']} / {decision['model']}")
assert decision["provider"] == "local", "Low complexity should be local"

# 3. Test High Complexity (Should be Cloud)
print("\n--- Test 2: High Complexity Task ---")
decision = router.route(task_complexity="high")
print(f"Decision: {decision['provider']} / {decision['model']}")
if "estimated_cost" in decision:
    budget.record_spend(decision["estimated_cost"])
    print(f"Recorded Spend. New Total: ${budget.get_current_spend()}")
    assert decision["provider"] == "anthropic", "High complexity should be Anthropic (Opus)"

# 4. Test Budget Overage Fallback
print("\n--- Test 3: Budget Overage ---")
budget.record_spend(10.0) # Max out budget
print(f"Budget Maxed Out: ${budget.get_current_spend()}")

decision = router.route(task_complexity="high")
print(f"Decision: {decision['provider']} / {decision['model']} (Reason: {decision['reason']})")
assert decision["provider"] == "local", "Should fallback to local when budget exceeded"

print("\n✅ Governor Logic Verified.")
