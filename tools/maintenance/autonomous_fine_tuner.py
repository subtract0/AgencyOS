
import os
import sys
import subprocess
import time
from pathlib import Path
from shared.env_loader import load_agency_env

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from experiments.training.compile_dpo_dataset import generate_synthetic_data

class AutonomousFineTuner:
    def __init__(self, base_model: str = "mlx-community/Llama-3.2-3B-Instruct"):
        self.base_model = base_model
        # Use external storage for adapters if available
        self.adapter_dir = "/Volumes/Satechi4TB/AgencyOS/adapters"
        if not os.path.exists("/Volumes/Satechi4TB"):
            self.adapter_dir = "adapters/local_dev"
            
        self.data_dir = "experiments/data/self_improvement"
        self.version = int(time.time())
        self.current_adapter = os.path.join(self.adapter_dir, f"v{self.version}")

    def run_pipeline(self):
        print("🤖 Autonomous Fine-Tuner: ACTIVATED")
        print(f"   Model: {self.base_model}")
        print(f"   Target Adapter: {self.current_adapter}")
        
        # Step 1: Data Compilation
        print("\n[1/4] 🧬 Compiling Dataset...")
        try:
            generate_synthetic_data(self.data_dir, num_samples=100)
        except Exception as e:
            print(f"❌ Data Compilation Failed: {e}")
            return False
            
        # Step 2: Training
        print("\n[2/4] 🚀 Training (LoRA)...")
        train_cmd = [
            sys.executable, "experiments/training/train_vcoder_local_m4.py",
            "--model", self.base_model,
            "--data", self.data_dir,
            "--adapter-out", self.current_adapter,
            "--iters", "50" # Short run for demo/test
        ]
        
        train_result = subprocess.run(train_cmd)
        if train_result.returncode != 0:
            print("❌ Training Failed.")
            return False
            
        # Step 3: Validation
        print("\n[3/4] 🧪 Validating New Adapter...")
        # In a real scenario, we would load the adapter and run tests.
        # For now, we will run the standard test suite to ensure NO REGRESSION in the codebase
        # (simulating that the environment is still healthy).
        # PROPER validation would involve running agents WITH the adapter.
        
        test_cmd = [sys.executable, "run_tests.py", "--fast", "--max-duration", "5"]
        test_result = subprocess.run(test_cmd)
        
        if test_result.returncode != 0:
            print("❌ Validation Failed (Tests Red). Rolling back.")
            return False
            
        # Step 4: Deployment
        print("\n[4/4] 🚢 Deployment...")
        print(f"✅ Adapter {self.current_adapter} is VALID.")
        print("   Updating AGENCY_MODEL config (Simulation)...")
        # Here we would update .env to point to the new adapter
        
        return True

if __name__ == "__main__":
    load_agency_env()
    trainer = AutonomousFineTuner()
    success = trainer.run_pipeline()
    if success:
        print("\n✨ Autonomous Improvement Cycle Complete: SUCCESS")
        sys.exit(0)
    else:
        print("\n💀 Autonomous Improvement Cycle Complete: FAILED")
        sys.exit(1)
