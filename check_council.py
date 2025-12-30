
import logging
import time
import requests
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO)

# Ensure imports work
sys.path.append(os.getcwd())
try:
    from tools.voice_v2.services.council_manager import CouncilManager
except ImportError:
    # Try adding parent parent to path if running from tools/voice_v2
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from tools.voice_v2.services.council_manager import CouncilManager

def test_council():
    cm = CouncilManager()
    logging.info("Starting Council for Test...")
    cm.start_council()
    
    # Wait longer for 70B to load. It takes time.
    logging.info("Waiting 45 seconds for models to load...")
    for i in range(45):
        time.sleep(1)
        if i % 5 == 0:
            print(f"Waiting... {i}/45s")
    
    ports = [8081, 8082, 8083]
    roles = ["Executive", "Engineer", "Architect"]
    
    all_good = True
    
    for port, role in zip(ports, roles):
        try:
            url = f"http://127.0.0.1:{port}/v1/models"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                logging.info(f"✅ {role} (Port {port}): ALIVE")
                logging.info(f"   Models: {resp.json()}")
            else:
                logging.error(f"❌ {role} (Port {port}): HTTP {resp.status_code}")
                all_good = False
        except Exception as e:
            logging.error(f"❌ {role} (Port {port}): FAILED ({e})")
            all_good = False
            
    logging.info("Stopping Council...")
    cm.stop_council()
    
    if all_good:
        print("SUCCESS: usage of 3 simultaneous models verified.")
        sys.exit(0)
    else:
        print("FAILURE: Some models failed to load.")
        sys.exit(1)

if __name__ == "__main__":
    test_council()
