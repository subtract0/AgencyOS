
import logging
import requests
from googlesearch import search
from tools.life.base import ToolResult, LifeTool

class ResearchTool(LifeTool):
    """
    A tool for "The Council" to research information online.
    Capabilities:
    - Web Search (Google)
    - Reddit Browsing (JSON API)
    - Report Writing
    """
    def __init__(self):
        super().__init__("ResearchTool", "A tool for deep internet research.")
        self.headers = {"User-Agent": "AgencyOS/1.0 (Macintosh; Intel Mac OS X 10_15_7)"}

    def get_capabilities(self):
        return ["search_web", "browse_reddit", "write_report"]

    def search_web(self, query: str, num_results: int = 5) -> str:
        """Performs a Google search and returns URLs/Titles."""
        try:
            results = []
            for j in search(query, num_results=num_results, advanced=True):
                results.append(f"- {j.title}: {j.url} ({j.description})")
            return "\n".join(results)
        except Exception as e:
            return f"Search failed: {e}"

    def browse_reddit(self, subreddit: str, sort: str = "top", time_filter: str = "day") -> str:
        """
        Browses a specific subreddit (e.g. 'LocalLLaMA') to find top posts.
        Sort: 'top', 'hot', 'new'.
        Time: 'day', 'week', 'month' (only for top).
        """
        try:
            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?t={time_filter}&limit=10"
            resp = requests.get(url, headers=self.headers)
            if resp.status_code != 200:
                return f"Failed to fetch Reddit: {resp.status_code}"
            
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            
            summary = []
            for post in posts:
                p = post["data"]
                title = p.get("title", "No Title")
                score = p.get("score", 0)
                url = p.get("url", "")
                selftext = p.get("selftext", "")[:200].replace("\n", " ") # Snippet
                summary.append(f"[{score} pts] {title} ({url})\n   Snippet: {selftext}...")
                
            return "\n\n".join(summary)
        except Exception as e:
            return f"Reddit browse error: {e}"

    def write_report(self, filename: str, content: str) -> str:
        """Writes a research report to ~/AgencyOS/Research/Reports/."""
        import os
        try:
            # Expand home directory
            base_dir = os.path.expanduser("~/AgencyOS/Research/Reports")
            os.makedirs(base_dir, exist_ok=True)
            
            # Sanitize filename
            safe_name = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in "._-"]).strip()
            if not safe_name.endswith(".md"):
                safe_name += ".md"
                
            path = os.path.join(base_dir, safe_name)
            
            with open(path, "w") as f:
                f.write(content)
                
            return f"Report saved successfully to: {path}"
        except Exception as e:
            return f"Failed to write report: {e}"

    # Tool Adapter Wrapper
    def get_tool_def(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search Google for a query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "browse_reddit",
                    "description": "Browse a subreddit for top posts.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subreddit": {"type": "string", "description": "Subreddit name (e.g. LocalLLaMA)."},
                            "sort": {"type": "string", "enum": ["top", "hot", "new"], "default": "top"},
                            "time_filter": {"type": "string", "enum": ["day", "week", "month"], "default": "day"}
                        },
                        "required": ["subreddit"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_report",
                    "description": "Save a markdown report to the filesystem.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Filename (e.g. 'Llama_Analysis.md')"},
                            "content": {"type": "string", "description": "The full markdown content."}
                        },
                        "required": ["filename", "content"]
                    }
                }
            }
        ]
        
    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        if tool_name == "search_web":
            result = self.search_web(kwargs.get("query", ""))
            return ToolResult(success=True, message=result)
        elif tool_name == "browse_reddit":
            result = self.browse_reddit(kwargs.get("subreddit", ""), kwargs.get("sort", "top"), kwargs.get("time_filter", "day"))
            return ToolResult(success=True, message=result)
        elif tool_name == "write_report":
            result = self.write_report(kwargs.get("filename", ""), kwargs.get("content", ""))
            return ToolResult(success=True, message=result)
        return ToolResult(success=False, message=f"Unknown tool: {tool_name}", error=f"Unknown tool: {tool_name}")
