"""
Real-time intelligence monitoring for local LLM capabilities
Tracks performance against AGI scale: 1-100 where 50=GPT-o3, 100=AGI
"""
import json
import time
from datetime import datetime
from pathlib import Path

class IntelligenceMonitor:
    def __init__(self, model_name="vcoder-120b"):
        self.model_name = model_name
        self.baseline_score = 37.5  # Initial estimate (35-40 range)
        self.metrics_file = Path("logs/intelligence_metrics.jsonl")
        self.metrics_file.parent.mkdir(exist_ok=True)
        
    def evaluate_task(self, task_type: str, success: bool, complexity: int, 
                     reasoning_quality: int, context_awareness: int):
        """
        Evaluate a single task and update intelligence score
        
        Args:
            task_type: 'refactor', 'debug', 'architecture', 'reasoning'
            success: Did it complete correctly?
            complexity: 1-10 (file size, dependencies, logic depth)
            reasoning_quality: 1-10 (pattern recognition, inference)
            context_awareness: 1-10 (systemic thinking, dependencies)
        """
        # Scoring rubric for o3-level (50/100)
        o3_benchmarks = {
            'refactor': {'success_rate': 0.95, 'complexity_handled': 8, 'reasoning': 7},
            'debug': {'success_rate': 0.90, 'complexity_handled': 7, 'reasoning': 8},
            'architecture': {'success_rate': 0.85, 'complexity_handled': 9, 'reasoning': 9},
            'reasoning': {'success_rate': 0.88, 'complexity_handled': 8, 'reasoning': 9},
        }
        
        benchmark = o3_benchmarks.get(task_type, o3_benchmarks['refactor'])
        
        # Calculate task score relative to o3
        task_score = 0
        if success:
            task_score += 40  # Base success weight
        
        # Complexity handling (max 30 points)
        complexity_ratio = complexity / benchmark['complexity_handled']
        task_score += min(30, 30 * complexity_ratio)
        
        # Reasoning quality (max 30 points)
        reasoning_ratio = reasoning_quality / benchmark['reasoning']
        task_score += min(30, 30 * reasoning_ratio)
        
        # Scale to 1-100 range where 50 = o3
        scaled_score = (task_score / 100) * 50
        
        metric = {
            'timestamp': datetime.now().isoformat(),
            'model': self.model_name,
            'task_type': task_type,
            'success': success,
            'complexity': complexity,
            'reasoning_quality': reasoning_quality,
            'context_awareness': context_awareness,
            'task_score': round(scaled_score, 2),
            'baseline_score': self.baseline_score,
        }
        
        # Log metric
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(metric) + '\n')
        
        return scaled_score
    
    def analyze_worker_performance(self, log_file="logs/autonomous_worker_v2.log"):
        """Analyze recent worker performance"""
        log_path = Path(log_file)
        if not log_path.exists():
            return None
            
        with open(log_path) as f:
            lines = f.readlines()
        
        successes = sum(1 for line in lines if "Successfully fixed" in line)
        failures = sum(1 for line in lines if "❌ Error fixing" in line or "didn't pass tests" in line)
        large_files = sum(1 for line in lines if "too large" in line)
        
        if successes + failures == 0:
            return None
        
        success_rate = successes / (successes + failures)
        
        # Evaluate based on observed behavior
        avg_complexity = 5 if large_files < 3 else 7  # Handling 500+ line files
        reasoning = 6  # Pattern replacement works, but no deep reasoning
        context = 4   # Misses __init__.py dependencies
        
        current_score = self.evaluate_task(
            'refactor', 
            success_rate > 0.80,
            avg_complexity,
            reasoning,
            context
        )
        
        return {
            'success_rate': success_rate,
            'successes': successes,
            'failures': failures,
            'current_score': current_score,
            'deviation': current_score - self.baseline_score
        }
    
    def generate_report(self):
        """Generate intelligence assessment report"""
        analysis = self.analyze_worker_performance()
        
        if not analysis:
            return "⏳ Insufficient data for assessment"
        
        report = f"""
🧠 Intelligence Assessment: {self.model_name}
{'='*60}

Current Score: {analysis['current_score']:.1f}/100
Baseline: {self.baseline_score:.1f}/100
Deviation: {analysis['deviation']:+.1f} points

Performance:
  Success Rate: {analysis['success_rate']*100:.1f}%
  Successes: {analysis['successes']}
  Failures: {analysis['failures']}

Comparison to o3 (50/100):
  Gap: {50 - analysis['current_score']:.1f} points
  Relative: {analysis['current_score']/50*100:.0f}% of o3 capability

Key Strengths:
  ✓ Fast iteration (20-40s per fix)
  ✓ Pattern recognition (import refactoring)
  ✓ Syntax validation

Key Weaknesses:
  ✗ No systemic reasoning (misses dependencies)
  ✗ Context limits (~400 lines)
  ✗ No architectural thinking

Path to o3-level (50/100):
  1. Implement chain-of-thought reasoning
  2. Add dependency graph awareness
  3. Increase context window to 32k+
  4. Add test generation capability
  5. Enable multi-step planning

Recommended Models for o3-level on M4 Max:
  • DeepSeek-R1 (70B MLX) - Strong reasoning
  • Qwen2.5-Coder (72B MLX) - Better context
  • Llama-3.3-70B-Instruct - Architectural thinking
"""
        return report

if __name__ == "__main__":
    monitor = IntelligenceMonitor()
    print(monitor.generate_report())
