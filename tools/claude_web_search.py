from litellm import Reasoning, responses
from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional, List, Union


class ClaudeWebSearch(BaseTool):
    """
    Sends an input request to the web search model and returns the results.
    """

    queries: Union[List[str], str] = Field(
        ...,
        description="The list of queries or questions to search the web for.",
        examples=[
            "How are files on openai uploaded?",
            "How does fast API integration work in agency-swarm? Provide a full code example."
        ]
    )
    links: Optional[List[str]] = Field(
        default=None,
        description="Optional list of links to use in web searches.",
        examples=[
            "https://platform.openai.com/docs/api-reference/files/create",
            "https://agency-swarm.ai/additional-features/fastapi-integration"
        ]
    )

    def run(self):
        if isinstance(self.queries, str):
            self.queries = [self.queries]
        try:
            response = responses(
                model="anthropic/claude-sonnet-4-20250514",
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that searches the web for information. "
                            "Simply use web search tool to answer user query. "
                            "Do not summarize search data and return the most relevant information exactly as it is. "
                            "You may navigate to other additional links if needed to answer the user's query."
                        )
                    },
                    {
                        "role": "user",
                        "content": "Please find an answer to the following queries: " + ", ".join(self.queries) + ". Use the following links if provided: " + ", ".join(self.links) if self.links else ""
                    }
                ],
                tools=[{
                    "type": "web_search_preview",
                    "search_context_size": "high"  # Options: "low", "medium" (default), "high"
                }],
                reasoning=Reasoning(effort="medium"),
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

    tool = ClaudeWebSearch(queries=["What is the latest version of the agency-swarm framework?", "How does fast API integration work in agency-swarm? Provide a full code example."], links=["https://platform.openai.com/docs/api-reference/files/create", "https://agency-swarm.ai/llms.txt"])
    print(tool.run())
