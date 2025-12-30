
from typing import Tuple, Dict, Any
from shared.budget_manager import BudgetManager

class ModelRouter:
    """
    Decides whether to route a task to Local Compute (Mac Studio) or Cloud API (Gemini/Opus).
    Enforces 'Local First' policy.
    """
    
    # Cost Estimates (approximate)
    COST_GEMINI_PRO_CALL = 0.05  # avg per turn
    COST_OPUS_CALL = 0.50        # avg per turn
    
    def __init__(self, budget_manager: BudgetManager):
        self.budget_manager = budget_manager

    def route(self, task_complexity: str = "low", force_cloud: bool = False) -> Dict[str, Any]:
        """
        Decides the best model for the task.
        
        Args:
            task_complexity: 'low' (Chat), 'medium' (Coding), 'high' (Architecture/Reasoning)
            force_cloud: User explicitly requested cloud model.
            
        Returns:
            Dict with provider, model, and cost_estimate.
        """
        
        # 1. Default to Local (Mac Studio)
        decision = {
            "provider": "local",
            "model": "llama-3.3-70b", # Our workhorse
            "reason": "Default policy: Local First"
        }
        
        # 2. Check for Cloud Escalation
        if force_cloud or task_complexity == "high":
            # Which model?
            if task_complexity == "high":
                target_model = "claude-3-5-opus"
                cost = self.COST_OPUS_CALL
            else:
                target_model = "gemini-1.5-pro"
                cost = self.COST_GEMINI_PRO_CALL
                
            # 3. Budget Check
            if self.budget_manager.check_budget(cost):
                decision = {
                    "provider": "anthropic" if "opus" in target_model else "google",
                    "model": target_model,
                    "reason": f"Escalated due to {task_complexity} complexity. Budget OK.",
                    "estimated_cost": cost
                }
            else:
                # Budget Failed: Fallback to Local + Warning
                decision = {
                    "provider": "local",
                    "model": "llama-3.3-70b",
                    "reason": "Budget Exceeded ($10 limit). Fallback to Local.",
                    "warning": "Budget Limit Reached"
                }

        return decision
