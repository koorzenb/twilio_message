"""Website scraper for monitoring updates."""

import os
import logging
import sys
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup

# Handle both relative imports (when used as module) and absolute imports (when run standalone)
try:
    from .base_website_scraper import BaseWebsiteScraper
except ImportError:
    # Add the parent directory to the path for standalone execution
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from base_website_scraper import BaseWebsiteScraper

logger = logging.getLogger(__name__)


class Scraper(BaseWebsiteScraper):
    """
    A scraper for monitoring the website for updates.
    """
    
    def __init__(self, base_url: str, history_file: str,  cache_file: str, cache_dir: str = "data",):
        """
        Initialize the scraper.
        
        Args:
            base_url: The URL of the website to scrape
            cache_dir: Directory to store cache files (will be created if it doesn't exist)
            cache_file: Name of the cache file for storing comparison data
            history_file: Name of the history file for storing change history
        """
        
        super().__init__(
            base_url=base_url,
            cache_dir=cache_dir,
            cache_file=cache_file,
            history_file=history_file
        )
    
    # Implementation of abstract methods from BaseWebsiteScraper
    
    def _extract_target_content(self, soup: BeautifulSoup) -> str:
        """Extract the specific target content we're monitoring for changes."""
        # Use the exact selector: body > main > section > gcds-date-modified
        target_element = soup.select_one('body > main > section > gcds-date-modified')
        
        if target_element:
            content = target_element.get_text(strip=True)
            logger.info(f"Target content found: {content}")
            return content
        else:
            # Fallback: try to find gcds-date-modified anywhere on the page
            fallback_element = soup.select_one('gcds-date-modified')
            if fallback_element:
                content = fallback_element.get_text(strip=True)
                logger.info(f"Target content found (fallback): {content}")
                return content
            else:
                logger.warning("Target content (gcds-date-modified) not found")
                return "Target content not found"
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the page title."""
        title_element = soup.find('title')
        return title_element.get_text(strip=True) if title_element else "No title found"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content of the page."""
        # Look for common content containers
        content_selectors = [
            'main',
            '.main-content',
            '#content',
            '.content',
            'article',
            '.gc-main'
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True)[:1000]  # Limit to first 1000 chars
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return body.get_text(strip=True)[:1000]
        
        return "No main content found"
    
    def _extract_important_notices(self, soup: BeautifulSoup) -> List[str]:
        """Extract important notices or alerts from the page."""
        notices = []
        
        # Look for common notice/alert patterns
        notice_selectors = [
            '.alert',
            '.notice',
            '.important',
            '.warning',
            '.announcement',
            '.gc-ntc'
        ]
        
        for selector in notice_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Only include substantial notices
                    notices.append(text)
        
        return notices

def check_updates(scraper: BaseWebsiteScraper, current_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Convenience function to check for sponsor parents website updates.
    
    Args:
        current_data: Optional pre-scraped website data. If None, will scrape automatically.
    
    Returns:
        bool: True if updates detected, False otherwise
    """
    return scraper.check_for_updates(current_data)

def main():
    """Main function for running the scraper as a standalone script."""
    import argparse
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Sponsor Parents Website Scraper')
    parser.add_argument(
        '--action', 
        choices=['scrape', 'check-updates', 'history'], 
        default='scrape',
        help='Action to perform (default: scrape)'
    )
    parser.add_argument(
        '--history-limit', 
        type=int, 
        default=10,
        help='Number of history entries to show (default: 10)'
    )
    parser.add_argument(
        '--cache-dir',
        default='data',
        help='Directory to store cache files (default: data)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.action == 'scrape':
            print("Scraping sponsor parents website...")
            base_url = "https://www.amazon.ca/s?k=xbox+series+s&crid=2UH8F14M7IDR9&sprefix=xbox+series+s%2Caps%2C1027&ref=nb_sb_noss_1"
            history_file = "xbox_amazon_history.json"
            scraper = Scraper(base_url=base_url, history_file=history_file, cache_dir=args.cache_dir, cache_file="xbox_cache.json")
            data = scraper.scrape_website_data()
            
            if data:
                print("Scraping successful!")
                print(f"Title: {data.get('title', 'N/A')}")
                print(f"Price: {data.get('price', 'N/A')}")
                print(f"URL: {data.get('url', 'N/A')}")
                print(f"Page size: {data.get('page_size', 'N/A')} bytes")
                print(f"Important notices: {len(data.get('important_notices', []))} found")
                
                if data.get('important_notices'):
                    print("\nImportant notices:")
                    for i, notice in enumerate(data['important_notices'], 1):
                        print(f"  {i}. {notice[:100]}...")
                        
            else:
                print("Scraping failed!")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Unexpected error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()