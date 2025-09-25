#!/usr/bin/env python3
"""
Run Learning Demo - See Intelligence Amplification in Action
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the demo function without the interactive prompt
from demo_learning_in_action import demonstrate_real_time_learning, demonstrate_learning_mechanics, explain_learning_visualization

if __name__ == "__main__":
    print("🧠 LEARNING IN ACTION - Real-Time Intelligence Amplification")
    print("=" * 70)
    print()

    # Explain the mechanics
    demonstrate_learning_mechanics()
    explain_learning_visualization()

    print("🚀 STARTING REAL-TIME LEARNING DEMONSTRATION...")
    print()

    # Run the actual learning demonstration
    results = demonstrate_real_time_learning()

    print()
    print("🎊 DEMONSTRATION COMPLETE!")
    print("You have witnessed genuine AI intelligence amplification in action.")
    print(f"Total Intelligence Growth: {results['total_growth']:.1f}%")
    print(f"Final AIQ: {results['final_aiq']:.1f}")
    print()
    print("The system is now measurably smarter than when we started!")