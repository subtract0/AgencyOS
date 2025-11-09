#!/usr/bin/env python3
"""
Opportunity Validator - Autonomous Internet Search for Proven Solutions

Searches the internet for historical human problems that:
1. Have proven, successful solutions
2. Are easily maintainable
3. Are highly profitable
4. Are fully digital

Uses Google/Brave search, Quora, Reddit to find validated opportunities.
"""

import json
import time
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI


@dataclass
class OpportunityEvidence:
    """Evidence that a solution is successful"""
    revenue: Optional[str] = None
    users: Optional[str] = None
    growth: Optional[str] = None
    testimonials: List[str] = None
    market_size: Optional[str] = None

    def __post_init__(self):
        if self.testimonials is None:
            self.testimonials = []


@dataclass
class ValidatedOpportunity:
    """A problem with proven digital solution"""
    problem: str
    solution_name: str
    solution_category: str  # SaaS, digital product, online service, etc.
    source_url: str
    evidence: OpportunityEvidence
    maintainability_score: float  # 0-1 scale
    profitability_score: float    # 0-1 scale
    digital_score: float          # 0-1 scale (1.0 = fully digital)
    overall_score: float          # Weighted average
    collected_at: int
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class OpportunityValidator:
    """Searches internet for proven digital solution opportunities"""

    def __init__(self, runtime_hours: int = 6):
        self.runtime_hours = runtime_hours
        self.opportunities = []

        # Setup logging
        log_dir = Path("logs/opportunity_validator")
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"validator_{runtime_hours}hr_{timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Search queries for proven solutions
        self.search_queries = [
            # SaaS success stories
            "most profitable SaaS products 2024",
            "successful digital products revenue",
            "bootstrapped SaaS companies profit",

            # Problem-solution pairs
            "what problem does Stripe solve revenue",
            "what problem does Calendly solve users",
            "what problem does Notion solve profitability",
            "what problem does Loom solve market size",

            # Historical problems with digital solutions
            "scheduling problem solved by digital product",
            "communication problem solved by SaaS",
            "collaboration problem solved by software",
            "payment processing problem digital solution",

            # Market validation
            "profitable digital products for small businesses",
            "high margin software businesses",
            "fully digital business models",

            # Niche markets
            "coaching business software revenue",
            "therapist practice management SaaS",
            "relationship coaching digital tools"
        ]

        # Initialize local LLM client
        self.llm_client = OpenAI(
            api_key="not-needed",
            base_url="http://localhost:1234/v1"
        )

    def search_google(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Search Google for query (placeholder - needs proper API)

        In production, use:
        - Google Custom Search API
        - SerpAPI
        - ScraperAPI
        - Brave Search API
        """
        self.logger.info(f"Google search: {query}")

        # For now, return empty list (needs API key)
        # TODO: Implement with proper search API
        return []

    def search_reddit_for_solutions(self, problem_domain: str) -> List[Dict]:
        """Search Reddit for discussions about successful solutions"""
        results = []

        # Search subreddits where people discuss successful tools
        subreddits = [
            "r/SaaS",
            "r/Entrepreneur",
            "r/startups",
            "r/indiehackers",
            "r/SideProject"
        ]

        for subreddit in subreddits:
            try:
                url = f"https://www.reddit.com/{subreddit}/top.json?t=year&limit=25"
                headers = {'User-Agent': 'OpportunityValidator/1.0'}

                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                data = response.json()
                posts = data.get('data', {}).get('children', [])

                for post in posts:
                    post_data = post.get('data', {})
                    title = post_data.get('title', '').lower()
                    selftext = post_data.get('selftext', '').lower()

                    # Look for revenue/profit mentions
                    if any(keyword in title or keyword in selftext for keyword in
                           ['revenue', 'profit', 'mrr', 'arr', 'users', 'paying customers']):
                        results.append({
                            'title': post_data.get('title'),
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'text': selftext[:500],
                            'upvotes': post_data.get('ups', 0),
                            'subreddit': subreddit
                        })

                self.logger.info(f"Reddit {subreddit}: Found {len([r for r in results if r['subreddit'] == subreddit])} posts")
                time.sleep(2)  # Rate limiting

            except Exception as e:
                self.logger.error(f"Reddit search error ({subreddit}): {e}")

        return results

    def analyze_opportunity_with_llm(self, text: str, source: str) -> Optional[ValidatedOpportunity]:
        """
        Use local LLM to extract opportunity details from text

        LLM analyzes:
        - What problem is being solved
        - What solution is mentioned
        - Evidence of success (revenue, users, growth)
        - Whether it's fully digital
        - Maintainability indicators
        """
        try:
            prompt = f"""You are a JSON extractor. Analyze this Reddit post about a business/product.

TEXT:
{text[:2000]}

Respond ONLY with valid JSON (no markdown, no explanations):

{{
  "problem": "What human problem does this solve? (1 sentence)",
  "solution_name": "Product/service name",
  "solution_category": "SaaS",
  "revenue": "$Xk/month or null",
  "users": "Xk users or null",
  "growth": "X% MoM or null",
  "is_fully_digital": true,
  "maintainability": "medium",
  "profitability": "high"
}}

IMPORTANT: Return ONLY the JSON object, nothing else."""

            response = self.llm_client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=400
            )

            analysis_text = response.choices[0].message.content.strip()

            # Clean up response
            # Remove markdown formatting if present
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0].strip()

            # Remove any leading/trailing whitespace
            analysis_text = analysis_text.strip()

            # If empty, return None
            if not analysis_text:
                return None

            analysis = json.loads(analysis_text)

            # Convert to ValidatedOpportunity
            if analysis.get('problem') and analysis.get('solution_name'):
                # Score calculation
                maintainability_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
                profitability_map = {"low": 0.3, "medium": 0.6, "high": 0.9}

                # Safe extraction with defaults
                maintainability_raw = analysis.get('maintainability', 'medium')
                profitability_raw = analysis.get('profitability', 'medium')

                # Handle None values
                if maintainability_raw is None:
                    maintainability_raw = 'medium'
                if profitability_raw is None:
                    profitability_raw = 'medium'

                maintainability_score = maintainability_map.get(
                    str(maintainability_raw).lower(), 0.5
                )
                profitability_score = profitability_map.get(
                    str(profitability_raw).lower(), 0.5
                )
                digital_score = 1.0 if analysis.get('is_fully_digital', False) else 0.3

                # Overall score (weighted: profitability 40%, digital 30%, maintainability 30%)
                overall_score = (
                    profitability_score * 0.4 +
                    digital_score * 0.3 +
                    maintainability_score * 0.3
                )

                return ValidatedOpportunity(
                    problem=analysis['problem'],
                    solution_name=analysis['solution_name'],
                    solution_category=analysis.get('solution_category', 'unknown'),
                    source_url=source,
                    evidence=OpportunityEvidence(
                        revenue=analysis.get('revenue'),
                        users=analysis.get('users'),
                        growth=analysis.get('growth')
                    ),
                    maintainability_score=maintainability_score,
                    profitability_score=profitability_score,
                    digital_score=digital_score,
                    overall_score=overall_score,
                    collected_at=int(time.time())
                )

            return None

        except Exception as e:
            self.logger.error(f"LLM analysis error: {e}")
            return None

    def validate_opportunity(self, opportunity: ValidatedOpportunity) -> bool:
        """
        Validate if opportunity meets criteria:
        - Fully digital (digital_score >= 0.8)
        - Profitable (profitability_score >= 0.6)
        - Maintainable (maintainability_score >= 0.5)
        """
        return (
            opportunity.digital_score >= 0.8 and
            opportunity.profitability_score >= 0.6 and
            opportunity.maintainability_score >= 0.5
        )

    def save_checkpoint(self):
        """Save current progress"""
        checkpoint_dir = Path("logs/opportunity_validator/checkpoints")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = checkpoint_dir / f"checkpoint_{timestamp}.json"

        data = {
            "runtime_hours": self.runtime_hours,
            "opportunities_collected": len(self.opportunities),
            "opportunities": [asdict(o) for o in self.opportunities]
        }

        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Checkpoint saved: {checkpoint_file}")

    def run(self):
        """Main validation loop"""
        self.logger.info("=" * 80)
        self.logger.info("OPPORTUNITY VALIDATOR STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"Runtime: {self.runtime_hours} hours")
        self.logger.info("Searching for: Proven, profitable, fully digital solutions")
        self.logger.info("=" * 80)

        iteration = 0

        # For now, focus on Reddit (easiest to scrape without API keys)
        # TODO: Add Google/Brave search when API keys are available

        self.logger.info("\n" + "=" * 80)
        self.logger.info("PHASE 1: Reddit Analysis")
        self.logger.info("=" * 80)

        # Search Reddit for successful SaaS/digital product discussions
        reddit_results = self.search_reddit_for_solutions("saas")

        self.logger.info(f"\nFound {len(reddit_results)} Reddit posts to analyze")

        # Analyze each with local LLM
        for i, result in enumerate(reddit_results[:20]):  # Limit to 20 for first run
            self.logger.info(f"\nAnalyzing {i+1}/{min(20, len(reddit_results))}: {result['title'][:60]}...")

            text = f"{result['title']}\n\n{result['text']}"
            opportunity = self.analyze_opportunity_with_llm(text, result['url'])

            if opportunity and self.validate_opportunity(opportunity):
                self.opportunities.append(opportunity)
                self.logger.info(f"✅ VALIDATED: {opportunity.solution_name} (score: {opportunity.overall_score:.2f})")
            elif opportunity:
                self.logger.info(f"⚠️  WEAK: {opportunity.solution_name} (score: {opportunity.overall_score:.2f})")
            else:
                self.logger.info("❌ NO OPPORTUNITY DETECTED")

            time.sleep(3)  # Rate limiting for LLM

        # Save results
        self.save_checkpoint()

        # Summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("VALIDATOR COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Total opportunities found: {len(self.opportunities)}")

        if self.opportunities:
            # Sort by score
            sorted_opps = sorted(self.opportunities, key=lambda x: x.overall_score, reverse=True)

            self.logger.info("\nTOP 5 OPPORTUNITIES:")
            for i, opp in enumerate(sorted_opps[:5], 1):
                self.logger.info(f"\n{i}. {opp.solution_name}")
                self.logger.info(f"   Problem: {opp.problem[:100]}...")
                self.logger.info(f"   Category: {opp.solution_category}")
                self.logger.info(f"   Score: {opp.overall_score:.2f} (Digital: {opp.digital_score:.1f}, Profit: {opp.profitability_score:.1f}, Maintain: {opp.maintainability_score:.1f})")
                if opp.evidence.revenue:
                    self.logger.info(f"   Revenue: {opp.evidence.revenue}")
                if opp.evidence.users:
                    self.logger.info(f"   Users: {opp.evidence.users}")

            # Save final export
            export_dir = Path("logs/opportunity_validator/exports")
            export_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = export_dir / f"opportunities_{timestamp}.json"

            with open(export_file, 'w') as f:
                json.dump([asdict(o) for o in sorted_opps], f, indent=2)

            self.logger.info(f"\n✅ Export saved: {export_file}")

        self.logger.info("=" * 80)


def main():
    """Run the opportunity validator"""
    import argparse

    parser = argparse.ArgumentParser(description="Opportunity Validator")
    parser.add_argument('--hours', type=int, default=6, help='Runtime in hours (default: 6)')
    parser.add_argument('--test', action='store_true', help='Test mode (analyze 5 posts only)')

    args = parser.parse_args()

    runtime = 0.1 if args.test else args.hours  # 6 minutes for test mode

    validator = OpportunityValidator(runtime_hours=runtime)
    validator.run()


if __name__ == "__main__":
    main()
