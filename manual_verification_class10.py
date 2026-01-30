import sys
import os

# Ensure we can import cells
sys.path.append(os.getcwd())

from cells.action.action_cell import ActionCell

def test_interactive_shell():
    print("🚀 Starting Class 10 Verification: Interactive Shell")
    cell = ActionCell()
    
    # We ask it to use the tool explicitly
    signal = "Use the 'run_interactive_shell' tool to execute 'ls -la' and show me the output."
    
    print(f"🔴 Signal: {signal}")
    result = cell.process_signal(signal)
    
    print("\n✅ Result from ActionCell:")
    print(result)

if __name__ == "__main__":
    test_interactive_shell()
