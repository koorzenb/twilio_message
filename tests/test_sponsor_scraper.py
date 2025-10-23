"""Test script for sponsor parents scraper with enhanced persistent caching."""

import sys
import os
# Add the src directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.sponsor_parents_scraper import (
    SponsorParentsScraper, 
    check_sponsor_parents_updates,
    get_sponsor_parents_history
)

def test_enhanced_scraper():
    """Test the enhanced sponsor parents scraper with persistent caching."""
    print("Testing Enhanced Sponsor Parents Scraper with Persistent Caching...")
    
    # Test basic scraping
    scraper = SponsorParentsScraper()
    data = scraper.scrape_website_data()
    
    if data:
        print("✅ Scraping successful!")
        print(f"Title: {data.get('title', 'N/A')}")
        print(f"Target content: {data.get('target_content', 'N/A')}")
        print(f"Target content hash: {data.get('target_content_hash', 'N/A')}")
        print(f"Page size: {data.get('page_size', 'N/A')} bytes")
        print(f"Last updated: {data.get('last_updated', 'N/A')}")
        print(f"Important notices: {len(data.get('important_notices', []))} found")
        
        # Check cache directory
        cache_dir = scraper.cache_dir
        print(f"\n📁 Cache directory: {cache_dir}")
        if os.path.exists(cache_dir):
            cache_files = os.listdir(cache_dir)
            print(f"Cache files: {cache_files}")
        
    else:
        print("❌ Scraping failed!")
    
    # Test update detection
    print("\n🔍 Testing update detection...")
    has_updates = check_sponsor_parents_updates()
    print(f"Updates detected: {has_updates}")
    
    # Test history retrieval
    print("\n📊 Testing change history...")
    history = get_sponsor_parents_history(5)
    if history:
        print(f"Found {len(history)} history entries:")
        for i, entry in enumerate(history, 1):
            print(f"  {i}. {entry.get('timestamp', 'N/A')} - {entry.get('change_reason', 'N/A')}")
    else:
        print("No history entries found")
    
    # Show persistent file locations
    print(f"\n💾 Persistent storage locations:")
    print(f"  Main cache: {scraper.cache_file}")
    print(f"  Backup cache: {scraper.backup_file}")
    print(f"  History file: {scraper.history_file}")
    
    # Check if files exist
    for file_path, name in [
        (scraper.cache_file, "Main cache"),
        (scraper.backup_file, "Backup cache"),
        (scraper.history_file, "History file")
    ]:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✅ {name}: {size} bytes")
        else:
            print(f"  ❌ {name}: Not found")

if __name__ == "__main__":
    test_enhanced_scraper()