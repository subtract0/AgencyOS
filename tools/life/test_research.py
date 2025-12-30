
from tools.life.research_tool import ResearchTool

def test_research():
    rt = ResearchTool()
    
    print("Testing Google Search...")
    res = rt.search_web("latest local llm models reddit")
    print(res[:200] + "...")
    
    print("\nTesting Reddit Browse (r/LocalLLaMA)...")
    res_reddit = rt.browse_reddit("LocalLLaMA", sort="top", time_filter="week")
    if "Failed" in res_reddit or "error" in res_reddit.lower():
        print("❌ Reddit Failed:", res_reddit)
    else:
        print("✅ Reddit Success!")
        print(res_reddit[:300] + "...")

if __name__ == "__main__":
    test_research()
