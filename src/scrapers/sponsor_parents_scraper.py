"""Sponsor Parents website scraper for monitoring updates."""

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


class SponsorParentsScraper(BaseWebsiteScraper):
    """
    A scraper for monitoring the Sponsor Parents website for updates.
    """
    
    def __init__(self, cache_dir: str = "data", cache_file: str = "sponsor_parents_cache.json"):
        """
        Initialize the Sponsor Parents scraper.
        
        Args:
            cache_dir: Directory to store cache files (will be created if it doesn't exist)
            cache_file: Name of the cache file for storing comparison data
        """
        base_url = "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/family-sponsorship/sponsor-parents-grandparents.html"
        history_file = "sponsor_parents_history.json"
        
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
    
    def _extract_last_updated(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the last updated date if available."""
        # Look for common "last updated" patterns specific to Canada.ca
        update_selectors = [
            '.last-updated',
            '.date-modified',
            '.updated',
            '.modification-date',
            'gcds-date-modified'  # Government of Canada Design System
        ]
        
        for selector in update_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None


# Convenience functions for easy usage
def scrape_sponsor_parents_data() -> Optional[Dict[str, Any]]:
    """
    Convenience function to scrape sponsor parents website data.
    
    Returns:
        Dict containing scraped data or None if scraping fails
    """
    scraper = SponsorParentsScraper()
    return scraper.scrape_website_data()


def check_sponsor_parents_updates() -> bool:
    """
    Convenience function to check for sponsor parents website updates.
    
    Returns:
        bool: True if updates detected, False otherwise
    """
    scraper = SponsorParentsScraper()
    return scraper.check_for_updates()


def get_sponsor_parents_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience function to get sponsor parents website change history.
    
    Args:
        limit: Maximum number of history entries to return
        
    Returns:
        List of historical change entries
    """
    scraper = SponsorParentsScraper()
    return scraper.get_change_history(limit)


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
            scraper = SponsorParentsScraper(cache_dir=args.cache_dir)
            data = scraper.scrape_website_data()
            
            if data:
                print("Scraping successful!")
                print(f"Title: {data.get('title', 'N/A')}")
                print(f"Target content: {data.get('target_content', 'N/A')}")
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
                
        elif args.action == 'check-updates':
            print("Checking for updates...")
            scraper = SponsorParentsScraper(cache_dir=args.cache_dir)
            has_updates = scraper.check_for_updates()
            
            if has_updates:
                print("Updates detected!")
                # Show the latest entry from history
                history = scraper.get_change_history(1)
                if history:
                    entry = history[0]
                    print(f"Timestamp: {entry.get('timestamp', 'N/A')}")
                    print(f"Target content: {entry.get('target_content', 'N/A')}")
                    print(f"Reason: {entry.get('change_reason', 'N/A')}")
            else:
                print("No updates detected")
                
        elif args.action == 'history':
            print(f"Showing last {args.history_limit} history entries...")
            scraper = SponsorParentsScraper(cache_dir=args.cache_dir)
            history = scraper.get_change_history(args.history_limit)
            
            if history:
                for i, entry in enumerate(history, 1):
                    print(f"\n{i}. {entry.get('timestamp', 'N/A')}")
                    print(f"   Target content: {entry.get('target_content', 'N/A')}")
                    print(f"   Reason: {entry.get('change_reason', 'N/A')}")
                    print(f"   Page size: {entry.get('page_size', 'N/A')} bytes")
            else:
                print("No history entries found")
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Unexpected error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()