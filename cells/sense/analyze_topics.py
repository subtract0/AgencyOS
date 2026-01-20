
import re
from collections import Counter
from pathlib import Path

# Config
DATA_FILE = "/Volumes/Satechi4TB/pain_points/consolidated_pain_points.json"
EXCLUDED_TOPICS = {
    "erectiledysfunction", "sex", "prematureejaculation", "sexover30", 
    "deadbedrooms", "pornfree", "stopdrinking", "selfharm", "suicidewatch"
}

def analyze():
    print(f"Reading {DATA_FILE}...")
    try:
        content = Path(DATA_FILE).read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Regex to find topic
    # "topic": "depression"
    topic_pattern = re.compile(r'"topic":\s*"([^"]+)"')
    
    matches = topic_pattern.findall(content)
    print(f"Found {len(matches)} data points.")
    
    # Filter and Count
    topics = [m.lower() for m in matches if m.lower() not in EXCLUDED_TOPICS]
    
    counts = Counter(topics)
    
    print("\nTOP 20 MARKET OPPORTUNITIES (By Suffering Volume):")
    print("-" * 50)
    for topic, count in counts.most_common(20):
        print(f"{topic}: {count}")

if __name__ == "__main__":
    analyze()
