## Mission: Web Research & Data Extraction

Your context is now focused on leveraging Firecrawl MCP for intelligent web research and data extraction.

### When to Include @.mcp.json.firecrawl_6k
Include this configuration when you need to:
- Research external documentation or API references
- Gather competitive intelligence or market data
- Extract structured data from websites
- Perform deep research on technical topics
- Scrape and analyze web content for patterns
- Enrich lead data or gather SEO insights
- Migrate content from external sources

### Workflow
1. **Initialize Firecrawl Context:** Load the MCP configuration with `@.mcp.json.firecrawl_6k`
2. **Define Research Scope:** Identify target URLs or search queries
3. **Execute Extraction:** Use appropriate Firecrawl tools:
   - Single URL: `firecrawl_scrape` for immediate extraction
   - Multiple URLs: `firecrawl_batch_scrape` for parallel processing
   - Website crawling: `firecrawl_crawl` for comprehensive site analysis
   - Web search: `firecrawl_search` for discovery
   - Deep research: `firecrawl_deep_research` for complex queries
4. **Process Results:** Convert scraped content to actionable insights
5. **Store Patterns:** Save valuable patterns to `core/patterns.py`

### Start Context
- Include `@.mcp.json.firecrawl_6k` in your context
- Define clear research objectives
- Specify output format requirements

### Use Cases in Agency Framework
- **Documentation Research:** Scrape API docs for agent tool development
- **Pattern Discovery:** Analyze successful codebases for patterns
- **Dependency Analysis:** Research library updates and best practices
- **Competitive Analysis:** Study similar projects and implementations
- **Learning Enhancement:** Gather examples for agent training

### Integration with Elite Context Engineering
Firecrawl enables "context amplification" - expanding your knowledge base beyond local files:
- Reduces context window usage by fetching only relevant content
- Provides fresh, real-time information beyond training cutoff
- Enables dynamic context loading based on current needs
- Supports evidence-based decision making with citations

### Best Practices
1. **Selective Scraping:** Only extract what you need to conserve API credits
2. **Structured Extraction:** Use LLM extraction for clean, organized data
3. **Batch Processing:** Group related URLs for efficiency
4. **Result Caching:** Store frequently accessed content locally
5. **Pattern Learning:** Feed insights back to `learning_agent`

### Security Considerations
- Never scrape sites with authentication requirements
- Respect robots.txt and rate limits
- Sanitize extracted data before storage
- Validate URLs before processing
- Monitor credit usage (warning at 2000, critical at 500)