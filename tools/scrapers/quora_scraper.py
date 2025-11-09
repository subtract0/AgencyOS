#!/usr/bin/env python3
"""
Quora Scraper with Cloudflare Bypass

Uses undetected-chromedriver to bypass Cloudflare protection.
Extracts pain points from Quora answers about coaching topics.
"""

import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("❌ Selenium/undetected-chromedriver not installed")
    print("Install with: pip install undetected-chromedriver selenium")
    exit(1)


@dataclass
class QuoraAnswer:
    """Quora Q&A data structure"""
    question: str
    answer: str
    url: str
    upvotes: int
    author: Optional[str] = None


class QuoraScraper:
    """Scrapes Quora with Cloudflare bypass"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def _init_driver(self):
        """Initialize undetected Chrome driver"""
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

        self.driver = uc.Chrome(options=options, version_main=None)
        self.logger.info("Chrome driver initialized")

    def search_topic(self, topic: str, max_results: int = 10) -> List[QuoraAnswer]:
        """
        Search Quora for topic and extract answers

        Args:
            topic: Search query (e.g., "divorce guilt")
            max_results: Max answers to collect

        Returns:
            List of QuoraAnswer objects
        """
        if not self.driver:
            self._init_driver()

        search_url = f"https://www.quora.com/search?q={topic.replace(' ', '+')}"
        self.logger.info(f"Searching Quora: {topic}")

        try:
            self.driver.get(search_url)
            time.sleep(3)  # Wait for Cloudflare check

            # Check if Cloudflare blocked us
            if "challenge" in self.driver.page_source.lower():
                self.logger.warning("Cloudflare challenge detected, waiting...")
                time.sleep(10)

            answers = []
            wait = WebDriverWait(self.driver, 10)

            # Find question links
            question_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/q/']")[:max_results]

            for i, link in enumerate(question_links):
                if len(answers) >= max_results:
                    break

                try:
                    url = link.get_attribute('href')
                    if not url or '/q/' not in url:
                        continue

                    self.logger.info(f"Scraping answer {i+1}/{max_results}: {url}")
                    answer = self._scrape_answer_page(url)

                    if answer:
                        answers.append(answer)
                        time.sleep(2)  # Rate limiting

                except Exception as e:
                    self.logger.error(f"Error scraping link: {e}")
                    continue

            self.logger.info(f"Collected {len(answers)} answers for '{topic}'")
            return answers

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    def _scrape_answer_page(self, url: str) -> Optional[QuoraAnswer]:
        """Scrape a single Quora answer page"""
        try:
            self.driver.get(url)
            time.sleep(2)

            # Extract question
            question_elem = self.driver.find_element(By.CSS_SELECTOR, "h1, [class*='question']")
            question = question_elem.text if question_elem else "Unknown"

            # Extract first answer
            answer_elems = self.driver.find_elements(By.CSS_SELECTOR, "[class*='answer'], .Answer")
            if not answer_elems:
                return None

            answer_text = answer_elems[0].text if answer_elems else ""

            # Extract upvotes (optional)
            upvotes = 0
            try:
                upvote_elem = self.driver.find_element(By.CSS_SELECTOR, "[class*='upvote']")
                upvote_text = upvote_elem.text
                upvotes = int(''.join(filter(str.isdigit, upvote_text))) if upvote_text else 0
            except:
                pass

            return QuoraAnswer(
                question=question,
                answer=answer_text,
                url=url,
                upvotes=upvotes
            )

        except Exception as e:
            self.logger.error(f"Failed to scrape {url}: {e}")
            return None

    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Driver closed")

    def __enter__(self):
        self._init_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def demo():
    """Demo Quora scraper"""
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("QUORA SCRAPER DEMO")
    print("=" * 80)
    print()

    topics = [
        "divorce guilt",
        "conscious uncoupling tips",
        "co-parenting struggles"
    ]

    with QuoraScraper(headless=False) as scraper:
        for topic in topics:
            print(f"\nSearching: {topic}")
            answers = scraper.search_topic(topic, max_results=3)

            print(f"Found {len(answers)} answers:")
            for i, answer in enumerate(answers, 1):
                print(f"\n{i}. {answer.question}")
                print(f"   Upvotes: {answer.upvotes}")
                print(f"   Answer: {answer.answer[:200]}...")
                print(f"   URL: {answer.url}")

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    demo()
