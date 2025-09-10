import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure project root is on sys.path so `agency_code_agent` can be imported
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables for tests (e.g., OPENAI_API_KEY)
load_dotenv()
