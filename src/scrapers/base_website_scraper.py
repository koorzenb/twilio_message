"""Generic website scraper base class for monitoring updates."""

import requests
import hashlib
import json
import os
import logging
from typing import Optional, Dict, Any, List, Callable
from bs4 import BeautifulSoup
from datetime import datetime
from abc import ABC, abstractmethod
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)


class BaseWebsiteScraper(ABC):
    """
    A generic base class for monitoring websites for updates.
    
    This class provides common functionality for web scraping, caching,
    change detection, and history tracking. Subclasses need to implement
    the site-specific extraction methods.
    """
    
    def __init__(
        self, 
        base_url: str,
        target_element: str,
        cache_dir: str = "data", 
        cache_file: str = "website_cache.json",
        history_file: str = "website_history.json",
        headers: Optional[Dict[str, str]] = None,
        use_selenium: bool = False
    ):
        """
        Initialize the website scraper.
        
        Args:
            base_url: The URL to scrape
            cache_dir: Directory to store cache files (will be created if it doesn't exist)
            cache_file: Name of the cache file for storing comparison data
            history_file: Name of the history file for storing change records
            headers: Custom HTTP headers for requests
            use_selenium: Whether to use Selenium instead of Requests for scraping
        """
        self.base_url = base_url
        self.target_element = target_element
        self.use_selenium = use_selenium
        
        # Create cache directory if it doesn't exist
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set up cache file paths
        self.cache_file = os.path.join(self.cache_dir, cache_file)
        self.backup_file = os.path.join(self.cache_dir, f"backup_{cache_file}")
        self.history_file = os.path.join(self.cache_dir, history_file)
        
        # Set up HTTP headers with defaults (updated for better Amazon compatibility)
        # Using simpler headers to avoid WAF fingerprinting (ConnectionResetError on canada.ca)
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        if headers:
            default_headers.update(headers)
        
        self.headers = default_headers
        self.session = requests.Session()
        return self.session
        
    def _fetch_with_selenium(self) -> str:
        """
        Fetch website content using Selenium WebDriver.
        
        Returns:
            str: The page source HTML
            
        Raises:
            Exception: If scraping fails
        """
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={self.headers['User-Agent']}")
        
        driver = None
        try:
            logger.info("Initializing Selenium WebDriver...")
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            
            logger.info("Fetching page with Selenium...")
            driver.get(self.base_url)
            
            # Allow some time for dynamic content to load
            time.sleep(3)
            
            return driver.page_source
            
        finally:
            if driver:
                driver.quit()

    def scrape_website_data(self, timeout: int = 30, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Scrape the website for relevant data.
        
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
                logger.info(f"Scraping website {self.base_url} (attempt {attempt + 1}/{max_retries})")
                
                content = None
                status_code = 200

                if self.use_selenium:
                    content = self._fetch_with_selenium()
                else:
                    response = self.session.get(self.base_url, timeout=timeout)
                    response.raise_for_status()
                    content = response.content
                    status_code = response.status_code
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract key information from the website using abstract methods
                scraped_data = {
                    'url': self.base_url,
                    'scraped_at': datetime.now().isoformat(),
                    'status_code': status_code,
                    'target_content': self._extract_target_content(soup),
                    'target_content_hash': self._generate_target_content_hash(soup),
                    'title': self._extract_title(soup),
                    'main_content': self._extract_main_content(soup),
                    'important_notices': self._extract_important_notices(soup),
                    'last_updated': self._extract_last_updated(soup),
                    'page_size': len(content),
                    'price': self.extract_price(soup),                    
                }
                
                # Allow subclasses to add additional data
                additional_data = self._extract_additional_data(soup)
                if additional_data:
                    scraped_data.update(additional_data)
                
                logger.info(f"Successfully scraped website {self.base_url}")
                return scraped_data
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")

            except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                last_exception = e
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                # Create a new session on connection errors to avoid reusing broken connections
                self.session = requests.Session()
                self.session.headers.update(self.headers)
                
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
    
    def check_for_updates(self, current_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if the website has been updated since last check.
        
        Args:
            current_data: Optional pre-scraped website data. If None, will scrape automatically.
        
        Returns:
            bool: True if the site has been updated, False otherwise
        """
        try:
            # Get current website data (scrape if not provided)
            if current_data is None:
                current_data = self.scrape_website_data()
                if not current_data:
                    logger.error("Failed to scrape current website data")
                    return False
            elif not isinstance(current_data, dict):
                logger.error("Invalid current_data parameter: must be a dictionary")
                return False
            
            # Load cached data
            cached_data = self._load_cached_data()
            
            # If no cached data exists, save current data and return True (first run)
            if not cached_data:
                logger.info("No cached data found, treating as first run (update detected)")
                self._save_cached_data(current_data)
                return True
            
            # Check for changes using the comparison strategy
            change_reason = self._detect_changes(current_data, cached_data)
            
            if change_reason:
                logger.info(f"Changes detected: {change_reason}")
                self._save_cached_data(current_data)
                self._add_to_history(current_data, change_reason)
                return True
            
            logger.info(f"No updates detected on {self.base_url}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False
    
    def _detect_changes(self, current_data: Dict[str, Any], cached_data: Dict[str, Any]) -> Optional[str]:
        """
        Detect changes between current and cached data.
        
        Args:
            current_data: Current scraped data
            cached_data: Previously cached data
            
        Returns:
            String describing the change if detected, None otherwise
        """
        # Compare target content hashes (most reliable)
        current_target_hash = current_data.get('target_content_hash')
        cached_target_hash = cached_data.get('target_content_hash')
        
        if current_target_hash != cached_target_hash:
            return "Target content changed"
        
        # Compare important notices
        current_notices = current_data.get('important_notices', [])
        cached_notices = cached_data.get('important_notices', [])
        
        if current_notices != cached_notices:
            return "Important notices changed"
        
        # Allow subclasses to implement additional change detection
        additional_changes = self._detect_additional_changes(current_data, cached_data)
        if additional_changes:
            return additional_changes
        
        return None
    
    def get_change_history(self, limit: int = 10) -> List[Dict[str, Any]]:
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
    
    # Abstract methods that subclasses must implement
    @abstractmethod
    def _extract_target_content(self, soup: BeautifulSoup) -> str:
        """Extract the specific target content for change monitoring."""
        pass
    
    @abstractmethod
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the page title."""
        pass
    
    @abstractmethod
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content of the page."""
        pass
    
    @abstractmethod
    def _extract_important_notices(self, soup: BeautifulSoup) -> List[str]:
        """Extract important notices or alerts from the page."""
        pass
    
    def extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract price information from the page."""
        update_selectors = [
            'div > span > div > div > div.a-section.a-spacing-small.puis-padding-left-small.puis-padding-right-small > div.a-section.a-spacing-none.a-spacing-top-small.s-price-instructions-style > div:nth-child(2) > div:nth-child(1) > a > span > span:nth-child(2) > span.a-price-whole',
            "div > div:nth-child(1) > div > div > div:nth-child(2) > span.b.lh-copy.dark-gray.f1.mr2 > span.inline-flex.flex-column > span"
        ]
        
        for selector in update_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    # Optional methods that subclasses can override
    def _extract_last_updated(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the last updated date if available."""
        # Default implementation looking for common patterns
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
    
    def _extract_additional_data(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract additional site-specific data. Override in subclasses."""
        return None
    
    def _detect_additional_changes(self, current_data: Dict[str, Any], cached_data: Dict[str, Any]) -> Optional[str]:
        """Detect additional site-specific changes. Override in subclasses."""
        return None
    
    # Helper methods
    def _generate_target_content_hash(self, soup: BeautifulSoup) -> str:
        """Generate hash of only the target content for more accurate change detection."""
        target_content = self._extract_target_content(soup)
        return hashlib.md5(target_content.encode('utf-8')).hexdigest()
    
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
            
            # Allow subclasses to add additional history data
            additional_history = self._get_additional_history_data(data)
            if additional_history:
                history_entry.update(additional_history)
            
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
    
    def _get_additional_history_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get additional data to store in history. Override in subclasses."""
        return None