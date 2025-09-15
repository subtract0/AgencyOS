from litellm import responses
from agency_swarm.tools import BaseTool
from pydantic import Field


class ClaudeWebSearch(BaseTool):
    """
    Sends an input request to the web search model and returns the results.
    """

    query: str = Field(..., description="The query to search the web for")

    def run(self):
        try:
            response = responses(
                model="anthropic/claude-sonnet-4-20250514",
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that can search the web for information. "
                            "Simply use web search tool to answer user query. "
                            "Do not summarize search data and return it as is. "
                        )
                    },
                    {
                        "role": "user",
                        "content": self.query
                    }
                ],
                tools=[{
                    "type": "web_search_preview",
                    "search_context_size": "medium"  # Options: "low", "medium" (default), "high"
                }],
                temperature=0,
            )
            return response.output[-1].content[-1].text
        except Exception as e:
            return f"Error reading file: {str(e)}"


# Create alias for Agency Swarm tool loading (expects class name = file name)
claude_web_search = ClaudeWebSearch

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # Test the tool
    # Test with current file
    current_file = __file__

    tool = ClaudeWebSearch(query="Get current price of bitcoin")
    print(tool.run())
