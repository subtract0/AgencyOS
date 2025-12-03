"""
Browser Tool
============

The "Window to the World" for AgencyOS.
Allows the agent to search the web and read content.

Capabilities:
- search: Find information (Google Search).
- visit: Read a webpage (Extract text).

Design:
- Lightweight: Uses requests + BeautifulSoup (no heavy browser).
- Text-First: Converts HTML to readable markdown for the agent.
"""

from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

# Optional dependency - falls back to mock mode if not installed
try:
    from googlesearch import search as google_search
    HAS_GOOGLE_SEARCH = True
except ImportError:
    google_search = None
    HAS_GOOGLE_SEARCH = False

from .base import LifeTool, ToolResult

class BrowserTool(LifeTool):
    def __init__(self, mock_mode: bool = False):
        super().__init__(
            name="Browser",
            description="Search the web and read pages."
        )
        self.mock_mode = mock_mode
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def get_capabilities(self) -> List[str]:
        return ["search", "visit"]

    def execute(self, action: str, **kwargs) -> ToolResult:
        if action == "search":
            return self.search(**kwargs)
        elif action == "visit":
            return self.visit(**kwargs)
        else:
            return ToolResult(success=False, message=f"Unknown action: {action}", error="InvalidAction")

    def search(self, query: str, num_results: int = 5) -> ToolResult:
        """
        Search Google for a query.
        Args:
            query: The search term.
            num_results: Number of results to return.
        """
        if self.mock_mode or not HAS_GOOGLE_SEARCH:
            # Return stable mock data for demos or when googlesearch not installed
            return ToolResult(
                success=True,
                message=f"Found 1 mock result for '{query}'" + (" (mock mode - googlesearch not installed)" if not HAS_GOOGLE_SEARCH else ""),
                data=[{
                    "title": "Luigi's Trattoria - Best Italian in SF",
                    "url": "https://luigis-sf-mock.com",
                    "description": "Authentic homemade pasta and wood-fired pizza in the heart of San Francisco. Rated 4.8 stars."
                }]
            )

        try:
            results = []
            # googlesearch-python yields URLs
            for url in google_search(query, num_results=num_results, advanced=True):
                results.append({
                    "title": url.title,
                    "url": url.url,
                    "description": url.description
                })
            
            if not results:
                return ToolResult(success=True, message=f"No results found for '{query}'.", data=[])

            summary = "\n".join([f"- [{r['title']}]({r['url']}): {r['description']}" for r in results])
            
            return ToolResult(
                success=True,
                message=f"Found {len(results)} results for '{query}':\n{summary}",
                data=results
            )
        except Exception as e:
            print(f"DEBUG: Search exception: {e}")
            return ToolResult(success=False, message=f"Search failed: {str(e)}", error="SearchError")

    def visit(self, url: str) -> ToolResult:
        """
        Visit a URL and extract text content.
        Args:
            url: The URL to visit.
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit length for agent context
            preview = text[:2000] + "..." if len(text) > 2000 else text
            
            return ToolResult(
                success=True,
                message=f"Read content from {url}:\n\n{preview}",
                data={"url": url, "content": text, "title": soup.title.string if soup.title else ""}
            )
            
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to visit {url}: {str(e)}", error="VisitError")
