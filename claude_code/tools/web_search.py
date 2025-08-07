from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Optional
import requests
import json
from urllib.parse import quote_plus
import time

class WebSearch(BaseTool):
    """
    Allows Claude to search the web and use the results to inform responses.
    
    - Provides up-to-date information for current events and recent data
    - Returns search result information formatted as search result blocks
    - Use this tool for accessing information beyond Claude's knowledge cutoff
    - Searches are performed automatically within a single API call
    
    Usage notes:
    - Domain filtering is supported to include or block specific websites
    - Web search is only available in the US
    - Account for "Today's date" in <env>. For example, if <env> says "Today's date: 2025-07-01", and the user wants the latest docs, do not use 2024 in the search query. Use 2025.
    """
    
    query: str = Field(..., min_length=2, description="The search query to use")
    allowed_domains: Optional[List[str]] = Field(None, description="Only include search results from these domains")
    blocked_domains: Optional[List[str]] = Field(None, description="Never include search results from these domains")
    
    def run(self):
        try:
            # Validate query length
            if len(self.query.strip()) < 2:
                return "Error: Search query must be at least 2 characters long"
            
            # In a production environment, this would use a real search API
            # For this implementation, we'll simulate search results
            return self._simulate_search_results()
            
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    
    def _simulate_search_results(self):
        """Simulate web search results since we don't have access to a real search API."""
        
        # Apply domain filters
        domain_filter_info = ""
        if self.allowed_domains:
            domain_filter_info += f"\\n(Filtering to domains: {', '.join(self.allowed_domains)})"
        if self.blocked_domains:
            domain_filter_info += f"\\n(Blocking domains: {', '.join(self.blocked_domains)})"
        
        # Simulate different types of search results based on query content
        query_lower = self.query.lower()
        
        # Programming/technical queries
        if any(term in query_lower for term in ['python', 'javascript', 'programming', 'code', 'api', 'github']):
            results = self._generate_tech_results()
        
        # News/current events
        elif any(term in query_lower for term in ['news', 'latest', 'recent', '2025', 'today']):
            results = self._generate_news_results()
        
        # Documentation/tutorials
        elif any(term in query_lower for term in ['how to', 'tutorial', 'guide', 'documentation', 'docs']):
            results = self._generate_docs_results()
        
        # General search
        else:
            results = self._generate_general_results()
        
        # Format the response
        response = f"🔍 Web Search Results for: '{self.query}'{domain_filter_info}\\n\\n"
        response += f"Found {len(results)} results:\\n\\n"
        
        for i, result in enumerate(results, 1):
            response += f"**Result {i}:** {result['title']}\\n"
            response += f"URL: {result['url']}\\n"
            response += f"Snippet: {result['snippet']}\\n"
            if result.get('date'):
                response += f"Date: {result['date']}\\n"
            response += "\\n"
        
        response += "\\n*Note: These are simulated search results. In a production environment, this would query a real search API.*"
        
        return response
    
    def _generate_tech_results(self):
        """Generate simulated technical/programming results."""
        return [
            {
                "title": "Official Documentation - Python.org",
                "url": "https://docs.python.org/3/",
                "snippet": "The official Python documentation with tutorials, library reference, and language reference.",
                "date": "2025-01-15"
            },
            {
                "title": "GitHub Repository - Popular Python Libraries", 
                "url": "https://github.com/vinta/awesome-python",
                "snippet": "A curated list of awesome Python frameworks, libraries, software and resources.",
                "date": "2025-01-10"
            },
            {
                "title": "Stack Overflow - Python Questions",
                "url": "https://stackoverflow.com/questions/tagged/python",
                "snippet": "Questions and answers about Python programming from the developer community.",
                "date": "2025-01-20"
            }
        ]
    
    def _generate_news_results(self):
        """Generate simulated news/current events results."""
        return [
            {
                "title": "Technology News Today - Latest Updates",
                "url": "https://techcrunch.com/2025/01/20/latest-tech-news",
                "snippet": "Breaking news and analysis on the latest technology developments and innovations.",
                "date": "2025-01-20"
            },
            {
                "title": "AI Developments in 2025 - Recent Breakthroughs",
                "url": "https://www.nature.com/articles/ai-2025-developments",
                "snippet": "Recent advances in artificial intelligence and machine learning research.",
                "date": "2025-01-18"
            },
            {
                "title": "Industry Report - Tech Trends 2025",
                "url": "https://www.mckinsey.com/tech-trends-2025",
                "snippet": "Analysis of emerging technology trends and their business impact in 2025.",
                "date": "2025-01-15"
            }
        ]
    
    def _generate_docs_results(self):
        """Generate simulated documentation/tutorial results."""
        return [
            {
                "title": "Complete Tutorial - Step by Step Guide",
                "url": "https://tutorial-site.com/complete-guide",
                "snippet": "A comprehensive tutorial covering all the basics with practical examples and exercises.",
                "date": "2024-12-15"
            },
            {
                "title": "Official Documentation - Getting Started",
                "url": "https://docs.example.com/getting-started",
                "snippet": "Official documentation with installation instructions, basic concepts, and examples.",
                "date": "2025-01-01"
            },
            {
                "title": "Video Tutorial Series - Learn in 30 Minutes",
                "url": "https://youtube.com/watch?v=tutorial123",
                "snippet": "Popular video tutorial series that explains concepts clearly with visual examples.",
                "date": "2024-12-20"
            }
        ]
    
    def _generate_general_results(self):
        """Generate simulated general search results."""
        return [
            {
                "title": "Wikipedia - Comprehensive Overview",
                "url": f"https://en.wikipedia.org/wiki/{quote_plus(self.query)}",
                "snippet": "Comprehensive encyclopedia article with detailed information, history, and references.",
                "date": "2025-01-10"
            },
            {
                "title": "Expert Analysis - In-Depth Article",
                "url": "https://expert-site.com/analysis",
                "snippet": "Detailed analysis from industry experts with insights and practical applications.",
                "date": "2025-01-05"
            },
            {
                "title": "Community Discussion - User Experiences",
                "url": "https://reddit.com/r/topic/discussions",
                "snippet": "Community discussions with user experiences, tips, and recommendations.",
                "date": "2025-01-12"
            }
        ]



# Create alias for Agency Swarm tool loading (expects class name = file name)
web_search = WebSearch

if __name__ == "__main__":
    # Test the tool with different types of queries
    
    # Test technical query
    tool1 = WebSearch(query="Python machine learning libraries 2025")
    result1 = tool1.run()
    print("Technical query result:")
    print(result1)
    
    # Test with domain filtering
    tool2 = WebSearch(
        query="latest AI news", 
        allowed_domains=["techcrunch.com", "nature.com"],
        blocked_domains=["spam-site.com"]
    )
    result2 = tool2.run()
    print("\\n" + "="*70 + "\\n")
    print("Domain-filtered query result:")
    print(result2)
    
    # Test tutorial query
    tool3 = WebSearch(query="how to create REST API tutorial")
    result3 = tool3.run()
    print("\\n" + "="*70 + "\\n") 
    print("Tutorial query result:")
    print(result3)