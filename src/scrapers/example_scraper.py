"""Example website scraper demonstrating how to use the BaseWebsiteScraper."""

import logging
from typing import Optional, List
from bs4 import BeautifulSoup
from .base_website_scraper import BaseWebsiteScraper

logger = logging.getLogger(__name__)


class ExampleWebsiteScraper(BaseWebsiteScraper):
    """
    Example scraper showing how to extend BaseWebsiteScraper for any website.
    
    This example scrapes a hypothetical news website, but the pattern can be
    applied to any website by implementing the required abstract methods.
    """
    
    def __init__(
        self, 
        base_url: str,
        cache_dir: str = "data", 
        cache_file: str = "example_cache.json",
        target_selector: str = "h1",  # CSS selector for the content to monitor
        notice_selectors: Optional[List[str]] = None
    ):
        """
        Initialize the example website scraper.
        
        Args:
            base_url: The URL to scrape
            cache_dir: Directory to store cache files
            cache_file: Name of the cache file
            target_selector: CSS selector for the main content to monitor for changes
            notice_selectors: List of CSS selectors for important notices
        """
        history_file = f"{cache_file.replace('.json', '')}_history.json"
        
        # Store site-specific configuration
        self.target_selector = target_selector
        self.notice_selectors = notice_selectors or [
            '.alert', '.notice', '.warning', '.announcement'
        ]
        
        super().__init__(
            base_url=base_url,
            cache_dir=cache_dir,
            cache_file=cache_file,
            history_file=history_file
        )
    
    # Implementation of required abstract methods
    
    def _extract_target_content(self, soup: BeautifulSoup) -> str:
        """Extract the specific target content for change monitoring."""
        target_element = soup.select_one(self.target_selector)
        
        if target_element:
            content = target_element.get_text(strip=True)
            logger.info(f"Target content found: {content[:100]}...")
            return content
        else:
            logger.warning(f"Target content not found with selector: {self.target_selector}")
            return "Target content not found"
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the page title."""
        title_element = soup.find('title')
        return title_element.get_text(strip=True) if title_element else "No title found"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content of the page."""
        # Try common content containers
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '#content',
            '.post-content'
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True)[:1000]  # Limit to 1000 chars
        
        # Fallback to body
        body = soup.find('body')
        if body:
            return body.get_text(strip=True)[:1000]
        
        return "No main content found"
    
    def _extract_important_notices(self, soup: BeautifulSoup) -> List[str]:
        """Extract important notices or alerts from the page."""
        notices = []
        
        for selector in self.notice_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 5:  # Only include substantial notices
                    notices.append(text)
        
        return notices


# Example usage functions
def create_news_scraper(news_url: str) -> ExampleWebsiteScraper:
    """
    Create a scraper for a news website.
    
    Args:
        news_url: URL of the news website
        
    Returns:
        Configured ExampleWebsiteScraper instance
    """
    return ExampleWebsiteScraper(
        base_url=news_url,
        cache_file="news_cache.json",
        target_selector="h1.headline, .article-title, h1",
        notice_selectors=['.breaking-news', '.alert', '.urgent']
    )


def create_blog_scraper(blog_url: str) -> ExampleWebsiteScraper:
    """
    Create a scraper for a blog website.
    
    Args:
        blog_url: URL of the blog
        
    Returns:
        Configured ExampleWebsiteScraper instance
    """
    return ExampleWebsiteScraper(
        base_url=blog_url,
        cache_file="blog_cache.json",
        target_selector=".post-title, h1, .entry-title",
        notice_selectors=['.notice', '.update', '.important']
    )


def create_generic_scraper(url: str, target_selector: str) -> ExampleWebsiteScraper:
    """
    Create a generic scraper for any website.
    
    Args:
        url: URL to scrape
        target_selector: CSS selector for the content to monitor
        
    Returns:
        Configured ExampleWebsiteScraper instance
    """
    # Create a cache file name based on the domain
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.replace('.', '_')
    cache_file = f"{domain}_cache.json"
    
    return ExampleWebsiteScraper(
        base_url=url,
        cache_file=cache_file,
        target_selector=target_selector
    )


if __name__ == "__main__":
    import argparse
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Example Website Scraper')
    parser.add_argument('url', help='URL to scrape')
    parser.add_argument('--target-selector', default='h1', 
                       help='CSS selector for target content (default: h1)')
    parser.add_argument('--action', choices=['scrape', 'check-updates', 'history'], 
                       default='scrape', help='Action to perform')
    parser.add_argument('--cache-dir', default='data', help='Cache directory')
    
    args = parser.parse_args()
    
    try:
        scraper = create_generic_scraper(args.url, args.target_selector)
        scraper.cache_dir = args.cache_dir
        
        if args.action == 'scrape':
            print(f"Scraping {args.url}...")
            data = scraper.scrape_website_data()
            if data:
                print("Scraping successful!")
                print(f"Title: {data.get('title')}")
                print(f"Target content: {data.get('target_content')}")
                print(f"Notices: {len(data.get('important_notices', []))}")
            else:
                print("Scraping failed!")
                sys.exit(1)
                
        elif args.action == 'check-updates':
            print("Checking for updates...")
            has_updates = scraper.check_for_updates()
            print(f"Updates detected: {has_updates}")
            
        elif args.action == 'history':
            print("Change history:")
            history = scraper.get_change_history(10)
            for entry in history:
                print(f"- {entry.get('timestamp')}: {entry.get('change_reason')}")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)