import sys
import os
sys.path.append(os.getcwd())
from tools.memory_aware_test_runner import get_safe_worker_count
import traceback

try:
    count = get_safe_worker_count()
    print(f"Worker count: {count}")
except Exception:
    traceback.print_exc()
