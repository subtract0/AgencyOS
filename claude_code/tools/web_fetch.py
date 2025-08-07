from agency_swarm.tools import BaseTool
from pydantic import Field
import requests
import time
from urllib.parse import urljoin, urlparse
try:
    from bs4 import BeautifulSoup
    import html2text
except ImportError:
    BeautifulSoup = None
    html2text = None

class WebFetch(BaseTool):
    """
    Fetches content from a specified URL and processes it using an AI model.
    
    - Fetches the URL content, converts HTML to markdown
    - Processes the content with the prompt using a small, fast model  
    - Returns the model's response about the content
    - Use this tool when you need to retrieve and analyze web content
    
    Usage notes:
    - IMPORTANT: If an MCP-provided web fetch tool is available, prefer using that tool instead of this one, as it may have fewer restrictions. All MCP-provided tools start with "mcp__".
    - The URL must be a fully-formed valid URL
    - HTTP URLs will be automatically upgraded to HTTPS
    - The prompt should describe what information you want to extract from the page
    - This tool is read-only and does not modify any files
    - Results may be summarized if the content is very large
    - Includes a self-cleaning 15-minute cache for faster responses when repeatedly accessing the same URL
    - When a URL redirects to a different host, the tool will inform you and provide the redirect URL in a special format. You should then make a new WebFetch request with the redirect URL to fetch the content.
    """
    
    url: str = Field(..., description="The URL to fetch content from")
    prompt: str = Field(..., description="The prompt to run on the fetched content")
    
    # Simple cache for repeated requests (in-memory, 15 minute TTL)
    _cache = {}
    _cache_ttl = 900  # 15 minutes
    
    def run(self):
        try:
            # Check if required libraries are available
            if BeautifulSoup is None or html2text is None:
                return "Error: Required libraries not available. Please install beautifulsoup4 and html2text: pip install beautifulsoup4 html2text"
            
            # Validate URL
            parsed_url = urlparse(self.url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return f"Error: Invalid URL format: {self.url}"
            
            # Upgrade HTTP to HTTPS
            if parsed_url.scheme == 'http':
                self.url = self.url.replace('http://', 'https://', 1)
                parsed_url = urlparse(self.url)
            
            # Check cache first
            cache_key = self.url
            current_time = time.time()
            
            if cache_key in self._cache:
                cached_data, cache_time = self._cache[cache_key]
                if current_time - cache_time < self._cache_ttl:
                    content = cached_data
                else:
                    # Clean expired cache entry
                    del self._cache[cache_key]
                    content = None
            else:
                content = None
            
            # Fetch content if not cached
            if content is None:
                content = self._fetch_url_content()
                if content.startswith("Error:"):
                    return content
                
                # Cache the result
                self._cache[cache_key] = (content, current_time)
                
                # Clean old cache entries (simple cleanup)
                for key in list(self._cache.keys()):
                    _, cache_time = self._cache[key]
                    if current_time - cache_time >= self._cache_ttl:
                        del self._cache[key]
            
            # Process content with the prompt
            return self._process_content_with_prompt(content)
            
        except Exception as e:
            return f"Error fetching web content: {str(e)}"
    
    def _fetch_url_content(self):
        """Fetch and convert URL content to markdown."""
        try:
            # Set up session with headers
            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Make the request with redirects handling
            response = session.get(
                self.url, 
                headers=headers, 
                timeout=30,
                allow_redirects=True
            )
            
            # Check if redirected to a different host
            final_url = response.url
            original_host = urlparse(self.url).netloc
            final_host = urlparse(final_url).netloc
            
            if original_host != final_host:
                return f"REDIRECT_TO_DIFFERENT_HOST: {final_url}\\n\\nThe URL {self.url} redirected to a different host: {final_url}. Please make a new WebFetch request with the redirect URL to fetch the content."
            
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            
            if 'html' not in content_type and 'xml' not in content_type:
                # Return raw text for non-HTML content
                return f"Content from {self.url} (Content-Type: {content_type}):\\n\\n{response.text[:10000]}"
            
            # Parse HTML and convert to markdown
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Convert to markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.ignore_emphasis = False
            h.body_width = 0  # Don't wrap lines
            
            markdown_content = h.handle(str(soup))
            
            # Clean up the markdown
            lines = markdown_content.split('\\n')
            clean_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and very short lines
                if len(line) > 2:
                    clean_lines.append(line)
            
            # Join and limit length
            clean_content = '\\n'.join(clean_lines)
            
            if len(clean_content) > 50000:
                clean_content = clean_content[:50000] + "\\n\\n[Content truncated due to length...]"
            
            return f"Content from {self.url}:\\n\\n{clean_content}"
            
        except requests.exceptions.Timeout:
            return f"Error: Request timed out after 30 seconds for URL: {self.url}"
        except requests.exceptions.RequestException as e:
            return f"Error fetching URL {self.url}: {str(e)}"
        except Exception as e:
            return f"Error processing content from {self.url}: {str(e)}"
    
    def _process_content_with_prompt(self, content):
        """Process the fetched content with the user's prompt."""
        # In a real implementation, this would use an AI model to process the content
        # For this implementation, we'll return the content with the prompt context
        
        max_content_length = 5000  # Reasonable limit for processing
        if len(content) > max_content_length:
            content_preview = content[:max_content_length] + "\\n\\n[Content truncated for processing...]"
        else:
            content_preview = content
        
        result = f"Processing web content with prompt: '{self.prompt}'\\n\\n"
        result += "="*60 + "\\n"
        result += content_preview
        result += "\\n" + "="*60 + "\\n\\n"
        result += f"Analysis based on prompt '{self.prompt}':\\n"
        result += "[In a production environment, this would be processed by an AI model to extract the requested information based on the prompt.]"
        
        return result



# Create alias for Agency Swarm tool loading (expects class name = file name)
web_fetch = WebFetch

if __name__ == "__main__":
    # Test the tool
    tool = WebFetch(
        url="https://httpbin.org/json",
        prompt="Extract the main data from this JSON response"
    )
    
    print("Testing WebFetch with httpbin JSON endpoint:")
    result = tool.run()
    print(result[:500] + "..." if len(result) > 500 else result)
    
    # Test with an HTML page
    tool2 = WebFetch(
        url="https://httpbin.org/html",
        prompt="What is the main heading of this HTML page?"
    )
    
    print("\\n" + "="*70 + "\\n")
    print("Testing WebFetch with httpbin HTML endpoint:")
    result2 = tool2.run()
    print(result2[:500] + "..." if len(result2) > 500 else result2)