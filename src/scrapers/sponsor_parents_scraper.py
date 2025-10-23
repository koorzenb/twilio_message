"""Sponsor Parents website scraper for monitoring updates."""

import requests
import hashlib
import json
import os
import logging
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)


class SponsorParentsScraper:
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
        self.base_url = "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/family-sponsorship/sponsor-parents-grandparents.html"
        
        # Create cache directory if it doesn't exist
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set up cache file paths
        self.cache_file = os.path.join(self.cache_dir, cache_file)
        self.backup_file = os.path.join(self.cache_dir, f"backup_{cache_file}")
        self.history_file = os.path.join(self.cache_dir, "sponsor_parents_history.json")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def scrape_website_data(self, timeout: int = 30, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Scrape the sponsor parents website for relevant data.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dict containing scraped data or None if scraping fails
            
        Raises:
            requests.RequestException: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Scraping sponsor parents website (attempt {attempt + 1}/{max_retries})")
                
                response = self.session.get(self.base_url, timeout=timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract key information from the website
                scraped_data = {
                    'url': self.base_url,
                    'scraped_at': datetime.now().isoformat(),
                    'status_code': response.status_code,
                    'target_content': self._extract_target_content(soup),
                    'target_content_hash': self._generate_target_content_hash(soup),
                    'title': self._extract_title(soup),
                    'main_content': self._extract_main_content(soup),
                    'important_notices': self._extract_important_notices(soup),
                    'last_updated': self._extract_last_updated(soup),
                    'page_size': len(response.content)
                }
                
                logger.info("Successfully scraped sponsor parents website")
                return scraped_data
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                
            if attempt < max_retries - 1:
                logger.info(f"Retrying in 2 seconds...")
                import time
                time.sleep(2)
        
        logger.error(f"Failed to scrape website after {max_retries} attempts: {last_exception}")
        return None
    
    def check_for_updates(self) -> bool:
        """
        Check if the sponsor parents website has been updated since last check.
        
        Returns:
            bool: True if the site has been updated, False otherwise
        """
        try:
            # Get current website data
            current_data = self.scrape_website_data()
            if not current_data:
                logger.error("Failed to scrape current website data")
                return False
            
            # Load cached data
            cached_data = self._load_cached_data()
            
            # If no cached data exists, save current data and return True (first run)
            if not cached_data:
                logger.info("No cached data found, treating as first run (update detected)")
                self._save_cached_data(current_data)
                return True
            
            # Compare target content hashes (more reliable than full page hash)
            current_target_hash = current_data.get('target_content_hash')
            cached_target_hash = cached_data.get('target_content_hash')
            
            if current_target_hash != cached_target_hash:
                logger.info("Target content (gcds-date-modified) has changed - update detected")
                self._save_cached_data(current_data)
                self._add_to_history(current_data, "Target content changed")
                return True
            
            # Also check if important notices have changed
            current_notices = current_data.get('important_notices', [])
            cached_notices = cached_data.get('important_notices', [])
            
            if current_notices != cached_notices:
                logger.info("Important notices have changed - update detected")
                self._save_cached_data(current_data)
                self._add_to_history(current_data, "Important notices changed")
                return True
            
            logger.info("No updates detected on sponsor parents website")
            return False
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False
    
    def _extract_target_content(self, soup: BeautifulSoup) -> str:
        """Extract the specific target content we're monitoring for changes."""
        # Use the exact selector you provided: body > main > section > gcds-date-modified
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
    
    def _generate_target_content_hash(self, soup: BeautifulSoup) -> str:
        """Generate hash of only the target content for more accurate change detection."""
        target_content = self._extract_target_content(soup)
        return hashlib.md5(target_content.encode('utf-8')).hexdigest()
    
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
    
    def _extract_important_notices(self, soup: BeautifulSoup) -> list:
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
        # Look for common "last updated" patterns
        update_selectors = [
            '.last-updated',
            '.date-modified',
            '.updated',
            '.modification-date'
        ]
        
        for selector in update_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate MD5 hash of the content for comparison."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _load_cached_data(self) -> Optional[Dict[str, Any]]:
        """Load cached data from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cached data: {e}")
        return None
    
    def _save_cached_data(self, data: Dict[str, Any]) -> None:
        """Save data to cache file with backup mechanism."""
        try:
            # Create backup of existing cache file
            if os.path.exists(self.cache_file):
                import shutil
                shutil.copy2(self.cache_file, self.backup_file)
                logger.info(f"Backup created: {self.backup_file}")
            
            # Save new data
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Cached data saved to {self.cache_file}")
            
        except Exception as e:
            logger.error(f"Error saving cached data: {e}")
            # Try to restore from backup if save failed
            if os.path.exists(self.backup_file):
                try:
                    import shutil
                    shutil.copy2(self.backup_file, self.cache_file)
                    logger.info("Restored cache from backup due to save failure")
                except Exception as restore_error:
                    logger.error(f"Failed to restore from backup: {restore_error}")
    
    def _add_to_history(self, data: Dict[str, Any], change_reason: str) -> None:
        """Add current scrape data to historical record."""
        try:
            # Load existing history
            history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # Add new entry
            history_entry = {
                'timestamp': data.get('scraped_at'),
                'target_content_hash': data.get('target_content_hash'),
                'target_content': data.get('target_content'),
                'change_reason': change_reason,
                'title': data.get('title'),
                'page_size': data.get('page_size'),
                'notices_count': len(data.get('important_notices', [])),
                'last_updated': data.get('last_updated')
            }
            
            history.append(history_entry)
            
            # Keep only last 100 entries to prevent file from growing too large
            if len(history) > 100:
                history = history[-100:]
            
            # Save updated history
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Added entry to history: {change_reason}")
            
        except Exception as e:
            logger.error(f"Error adding to history: {e}")
    
    def get_change_history(self, limit: int = 10) -> list:
        """
        Get the change history for the website.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of historical change entries
        """
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                return history[-limit:] if limit else history
        except Exception as e:
            logger.error(f"Error reading change history: {e}")
        return []


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


def get_sponsor_parents_history(limit: int = 10) -> list:
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
            print("🔍 Scraping sponsor parents website...")
            scraper = SponsorParentsScraper(cache_dir=args.cache_dir)
            data = scraper.scrape_website_data()
            
            if data:
                print("✅ Scraping successful!")
                print(f"📄 Title: {data.get('title', 'N/A')}")
                print(f"🎯 Target content: {data.get('target_content', 'N/A')}")
                print(f"🔗 URL: {data.get('url', 'N/A')}")
                print(f"📊 Page size: {data.get('page_size', 'N/A')} bytes")
                print(f"🔔 Important notices: {len(data.get('important_notices', []))} found")
                
                if data.get('important_notices'):
                    print("\n📢 Important notices:")
                    for i, notice in enumerate(data['important_notices'], 1):
                        print(f"  {i}. {notice[:100]}...")
                        
            else:
                print("❌ Scraping failed!")
                sys.exit(1)
                
        elif args.action == 'check-updates':
            print("🔍 Checking for updates...")
            scraper = SponsorParentsScraper(cache_dir=args.cache_dir)
            has_updates = scraper.check_for_updates()
            
            if has_updates:
                print("🆕 Updates detected!")
                # Show the latest entry from history
                history = scraper.get_change_history(1)
                if history:
                    entry = history[0]
                    print(f"📅 Timestamp: {entry.get('timestamp', 'N/A')}")
                    print(f"🎯 Target content: {entry.get('target_content', 'N/A')}")
                    print(f"📝 Reason: {entry.get('change_reason', 'N/A')}")
            else:
                print("✅ No updates detected")
                
        elif args.action == 'history':
            print(f"📊 Showing last {args.history_limit} history entries...")
            scraper = SponsorParentsScraper(cache_dir=args.cache_dir)
            history = scraper.get_change_history(args.history_limit)
            
            if history:
                for i, entry in enumerate(history, 1):
                    print(f"\n{i}. {entry.get('timestamp', 'N/A')}")
                    print(f"   🎯 Target content: {entry.get('target_content', 'N/A')}")
                    print(f"   📝 Reason: {entry.get('change_reason', 'N/A')}")
                    print(f"   📊 Page size: {entry.get('page_size', 'N/A')} bytes")
            else:
                print("📭 No history entries found")
                
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Unexpected error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()