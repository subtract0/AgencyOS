import json
import os
from datetime import datetime
from typing import Dict, Optional

class BudgetManager:
    """
    Manages the daily financial budget for the AgencyOS.
    Part of the 'Governor' Cell.
    Enforces the $10/day limit.
    """
    
    SETTINGS_DIR = ".agency"
    BUDGET_FILE = "budget_stats.json"
    DAILY_LIMIT_USD = 10.0
    
    def __init__(self, settings_dir: Optional[str] = None):
        if settings_dir:
            self.SETTINGS_DIR = settings_dir
        
        # Ensure stats directory exists
        os.makedirs(self.SETTINGS_DIR, exist_ok=True)
        self.stats_path = os.path.join(self.SETTINGS_DIR, self.BUDGET_FILE)
        self._load_stats()

    def _load_stats(self):
        """Loads stats or initializes a new day if date changed."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, 'r') as f:
                    data = json.load(f)
                    
                # Reset if new day
                if data.get("date") != today_str:
                    self.stats = {
                        "date": today_str,
                        "spend_usd": 0.0,
                        "requests": 0
                    }
                    self._save_stats()
                else:
                    self.stats = data
            except (json.JSONDecodeError, IOError):
                self.stats = {"date": today_str, "spend_usd": 0.0, "requests": 0}
        else:
            self.stats = {
                "date": today_str,
                "spend_usd": 0.0,
                "requests": 0
            }
            self._save_stats()

    def _save_stats(self):
        with open(self.stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def check_budget(self, estimated_cost: float = 0.0) -> bool:
        """
        Returns True if the spend is within budget.
        """
        self._load_stats() # Refresh in case other agents updated it
        return (self.stats["spend_usd"] + estimated_cost) <= self.DAILY_LIMIT_USD

    def record_spend(self, amount_usd: float):
        """Records a transaction cost."""
        self._load_stats() # Ensure we have latest
        self.stats["spend_usd"] += amount_usd
        self.stats["requests"] += 1
        self._save_stats() # Persist immediately
        
    def get_current_spend(self) -> float:
        self._load_stats()
        return self.stats["spend_usd"]

    def get_remaining_budget(self) -> float:
        return max(0.0, self.DAILY_LIMIT_USD - self.get_current_spend())
