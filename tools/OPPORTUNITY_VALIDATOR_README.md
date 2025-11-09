# Opportunity Validator

Autonomous internet search system that finds **historical human problems with proven, profitable, fully digital solutions**.

## Purpose

Instead of just collecting pain points, this system validates business opportunities by finding:
- ✅ Problems with existing successful solutions
- ✅ Fully digital products/services
- ✅ High profitability
- ✅ Easy maintainability

## How It Works

### 1. **Data Collection**
- Scrapes Reddit (r/SaaS, r/Entrepreneur, r/startups, r/indiehackers, r/SideProject)
- Searches for posts mentioning revenue, users, profitability
- Collects success stories with evidence

### 2. **LLM Analysis** (Local 120B Model)
Each post is analyzed to extract:
- **Problem**: What human problem does this solve?
- **Solution**: Product/service name and category
- **Evidence**: Revenue, users, growth metrics
- **Validation**: Is it digital? Profitable? Maintainable?

### 3. **Scoring System**
```
Overall Score = (Profitability × 40%) + (Digital × 30%) + (Maintainability × 30%)

- Profitability: low (0.3), medium (0.6), high (0.9)
- Digital: 0.3 (partial) to 1.0 (fully digital)
- Maintainability: low (0.3), medium (0.6), high (0.9)

Validation threshold: ≥ 0.8
```

### 4. **Output**
- JSON exports with validated opportunities
- Checkpoints for long-running sessions
- Detailed logs with analysis

## Usage

### Quick Test (5 posts)
```bash
export PYTHONPATH=/Users/am/Code/AgencyOS:
python tools/opportunity_validator.py --test
```

### Full 6-Hour Run
```bash
./tools/start_opportunity_validator.sh
```

### Background Monitoring
```bash
# Check logs
tail -f logs/opportunity_validator/validator_*.log

# Check results
cat logs/opportunity_validator/exports/opportunities_*.json
```

## Example Output

```json
{
  "problem": "Transcribing spoken audio (speech-to-text) for any web content",
  "solution_name": "Voicy",
  "solution_category": "SaaS",
  "evidence": {
    "revenue": "$3k/month",
    "users": "1k users",
    "growth": null
  },
  "maintainability_score": 0.6,
  "profitability_score": 0.9,
  "digital_score": 1.0,
  "overall_score": 0.84,
  "source_url": "https://reddit.com/r/SaaS/comments/..."
}
```

## Configuration

### Search Sources (Expandable)
- ✅ **Reddit** (implemented)
- 🔜 **Google Search** (requires SerpAPI key)
- 🔜 **Quora** (Selenium scraper available)
- 🔜 **Indie Hackers**
- 🔜 **Product Hunt**

### LLM Configuration
- **Model**: vcoder-120b-1.0-hi-mlx (local)
- **Endpoint**: http://localhost:1234/v1
- **Temperature**: 0.2 (low for structured extraction)
- **Max tokens**: 400

## Validation Criteria

An opportunity passes validation if:
1. **Digital score ≥ 0.8** (must be fully or mostly digital)
2. **Profitability score ≥ 0.6** (medium to high profitability)
3. **Maintainability score ≥ 0.5** (at least medium maintainability)
4. **Problem + solution clearly identified**
5. **Evidence of success** (revenue, users, or growth)

## File Structure

```
logs/opportunity_validator/
├── validator_6hr_TIMESTAMP.log      # Full log
├── checkpoints/
│   └── checkpoint_TIMESTAMP.json    # Progress snapshots
└── exports/
    └── opportunities_TIMESTAMP.json # Validated opportunities
```

## Differences from Pain Point Miner

| Feature | Pain Point Miner | Opportunity Validator |
|---------|------------------|----------------------|
| **Goal** | Find pain points | Find proven solutions |
| **Focus** | Emotional depth | Revenue validation |
| **Output** | Pain descriptions | Business opportunities |
| **Validation** | Authenticity score | Profitability + digital |
| **Use case** | Coaching insights | Market research |

## Next Steps

### To Run Autonomously for 6 Hours:
```bash
# Launch validator
./tools/start_opportunity_validator.sh 6

# Monitor progress
tail -f logs/opportunity_validator/*.log

# View results after completion
cat logs/opportunity_validator/exports/opportunities_*.json | jq
```

### To Add More Search Sources:
1. Implement new scraper method (e.g., `search_quora()`)
2. Call in `run()` method
3. Pass results to `analyze_opportunity_with_llm()`
4. LLM will extract and validate

### To Customize Validation:
Edit `validate_opportunity()` method in `tools/opportunity_validator.py`:
```python
def validate_opportunity(self, opportunity: ValidatedOpportunity) -> bool:
    return (
        opportunity.digital_score >= 0.8 and      # Adjust threshold
        opportunity.profitability_score >= 0.6 and
        opportunity.maintainability_score >= 0.5
    )
```

## Example Use Cases

1. **Market Research**: Find proven digital products in specific niches
2. **Competitive Analysis**: See what solutions exist for problems
3. **Opportunity Scouting**: Identify profitable digital business models
4. **Pattern Recognition**: Understand characteristics of successful solutions

## Requirements

- Python 3.9+
- `requests` (Reddit scraping)
- `openai` (local LLM client)
- `beautifulsoup4` (optional, for HTML parsing)
- Local LLM running at localhost:1234 (vcoder-120b)

## Cost

- **$0** - Fully local processing
- Reddit API: Free (public JSON endpoints)
- LLM: Local model (no API costs)
- Optional: Google Search API (~$5/1000 queries if enabled)

## Roadmap

- [ ] Add Google Custom Search integration
- [ ] Implement Quora scraping
- [ ] Add Product Hunt scraper
- [ ] Create dashboard for opportunity browsing
- [ ] Add VectorStore integration for pattern learning
- [ ] Build trend analysis (emerging opportunities)
- [ ] Add competitive landscape mapping
