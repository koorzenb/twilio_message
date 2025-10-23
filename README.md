# Twilio Message

Website monitoring system that detects changes and sends SMS notifications via Twilio.

## Quick Start

1. **Get Twilio credentials** - Sign up at [twilio.com](https://twilio.com)
2. **Set up environment** - Copy `.env.example` to `.env` and add your credentials
3. **Install dependencies** - Run `pip install -r src/requirements.txt`
4. **Run a scraper** - See commands below

## Available Scrapers

- **BurnSafe Scraper** - Nova Scotia burn restrictions
- **Sponsor Parents Scraper** - Canada.ca immigration updates  
- **Example Scraper** - Template for any website

## Creating Your Own Scraper

```python
from scrapers.base_website_scraper import BaseWebsiteScraper
from bs4 import BeautifulSoup
from typing import List

class YourWebsiteScraper(BaseWebsiteScraper):
    def __init__(self):
        super().__init__(
            base_url="https://example.com",
            cache_file="your_cache.json",
            history_file="your_history.json"
        )
    
    def _extract_target_content(self, soup: BeautifulSoup) -> str:
        # Extract the specific content you want to monitor
        element = soup.select_one('.important-content')
        return element.get_text(strip=True) if element else "Not found"
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        title = soup.find('title')
        return title.get_text(strip=True) if title else "No title"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        main = soup.find('main')
        return main.get_text(strip=True)[:1000] if main else "No content"
    
    def _extract_important_notices(self, soup: BeautifulSoup) -> List[str]:
        notices = []
        for notice in soup.select('.alert, .notice'):
            notices.append(notice.get_text(strip=True))
        return notices
```

## Running Scrapers

### Sponsor Parents Scraper

```bash
# Basic scraping (gets current website data)
python src/scrapers/sponsor_parents_scraper.py --action scrape

# Check for updates (compares with cached data)
python src/scrapers/sponsor_parents_scraper.py --action check-updates

# View change history
python src/scrapers/sponsor_parents_scraper.py --action history
```

### BurnSafe Scraper

```bash
# Run the main application (includes BurnSafe scraper + SMS notifications)
python src/main.py
```

### Import as Module

```python
from scrapers.sponsor_parents_scraper import (
    scrape_sponsor_parents_data,
    check_sponsor_parents_updates,
    get_sponsor_parents_history
)

# Get current data
data = scrape_sponsor_parents_data()

# Check for updates
has_updates = check_sponsor_parents_updates()

# Get change history
history = get_sponsor_parents_history(limit=5)
```

## Environment Variables (.env)

```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
MY_PHONE_NUMBER=your_recipient_phone_number
```

---

📋 **For detailed technical documentation, architecture details, and development guidelines, see [PRD.md](PRD.md)**
