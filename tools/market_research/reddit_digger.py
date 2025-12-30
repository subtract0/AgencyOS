
import requests
import json
import os
import time

class RedditDigger:
    def __init__(self):
        self.headers = {"User-Agent": "AgencyOS/MVP-Researcher/1.0"}
        self.pain_keywords = ["lonely", "broken", "divorce", "cheat", "suicide", "pointless", "fail", "pain", "struggle", "hopeless"]
        self.subreddits = ["lonely", "Divorce", "MensHealth", "depression", "socialanxiety", "malementalhealth"]

    def fetch_posts(self, subreddit, limit=50):
        url = f"https://www.reddit.com/r/{subreddit}/search.json?q={' OR '.join(self.pain_keywords)}&restrict_sr=1&sort=relevance&limit={limit}"
        # Fallback to hot if search fails or is strict? No, search is better for keywords.
        # Actually, let's just browse 'hot' and 'top' to see organic pain.
        
        # Strategy: Get TOP from last month to see what resonates.
        url = f"https://www.reddit.com/r/{subreddit}/top.json?t=month&limit={limit}"
        
        print(f"Fetching {subreddit}...")
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code != 200:
                print(f"Error {resp.status_code} for {subreddit}")
                return []
            
            data = resp.json()
            return data.get("data", {}).get("children", [])
        except Exception as e:
            print(f"Exception fetching {subreddit}: {e}")
            return []

    def analyze(self):
        report = "# Market Pain Report: The Cocoon MVP\n\n"
        report += "Captured 'Voice of Customer' for VSL Scripting.\n\n"
        
        all_posts = []
        
        for sub in self.subreddits:
            posts = self.fetch_posts(sub)
            for post in posts:
                p = post["data"]
                title = p.get("title", "")
                text = p.get("selftext", "")
                score = p.get("score", 0)
                url = p.get("url", "")
                
                # Filter for pain keywords in text to ensure relevance
                content_blob = (title + " " + text).lower()
                if any(k in content_blob for k in self.pain_keywords):
                    all_posts.append({
                        "sub": sub,
                        "title": title,
                        "text": text[:500] + "...", # Truncate
                        "score": score,
                        "url": url,
                        "pain_score": sum(content_blob.count(k) for k in self.pain_keywords)
                    })
            time.sleep(1) # Be nice to API

        # Sort by impact (Score + Pain count)
        all_posts.sort(key=lambda x: x["score"], reverse=True)
        
        # Top 20 Entries
        for i, p in enumerate(all_posts[:20]):
            report += f"## {i+1}. {p['title']} ({p['sub']} - {p['score']} pts)\n"
            report += f"**Source**: {p['url']}\n\n"
            report += f"> {p['text'].replace(chr(10), '\n> ')}\n\n"
            report += "---\n\n"
            
        # Save
        os.makedirs("tools/market_research", exist_ok=True)
        with open("tools/market_research/pain_points.md", "w") as f:
            f.write(report)
        print("Report saved to tools/market_research/pain_points.md")

if __name__ == "__main__":
    digger = RedditDigger()
    digger.analyze()
