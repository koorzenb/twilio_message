"""Test script for the burnafe scraper."""

import sys
import os
# Add the src directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.burnafe_scraper import get_burn_safe_status
from selenium import webdriver

def test_burnafe_scraper():
    """Test the BurnSafe scraper."""
    print("Testing BurnSafe Scraper...")
    
    # Set up WebDriver (this will be migrated to BeautifulSoup in Phase 1.4)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Test the burn safe status function
        print("🔥 Checking Nova Scotia burn status...")
        status = get_burn_safe_status(driver)
        
        if status:
            print(f"✅ Status retrieved: {status}")
        else:
            print("❌ Failed to retrieve status")
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        
    finally:
        # Clean up WebDriver
        driver.quit()
        print("🚗 WebDriver cleaned up")

if __name__ == "__main__":
    test_burnafe_scraper()