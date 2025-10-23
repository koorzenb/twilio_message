# twilio_message

Scrapes websites for important info and forwards to phone

## Getting Started

- Get a phone number from Twilio
- Set up environment variables (.env) for Twilio credentials and phone numbers
- Create a scraper using BeautifulSoup or Selenium
- see run.bat for example usage

## Available Scrapers

### 1. BurnSafe Scraper (Nova Scotia)

Monitors burn restrictions for Halifax County.

### 2. Sponsor Parents Scraper (Canada.ca)

Monitors the sponsor parents and grandparents immigration page for updates.

## Running Scrapers

### As Standalone Scripts

#### Sponsor Parents Scraper

```bash
# Basic scraping (gets current website data)
python src/scrapers/sponsor_parents_scraper.py --action scrape

# Check for updates (compares with cached data)
python src/scrapers/sponsor_parents_scraper.py --action check-updates

# View change history
python src/scrapers/sponsor_parents_scraper.py --action history

# View more history entries
python src/scrapers/sponsor_parents_scraper.py --action history --history-limit 20

# Use custom cache directory
python src/scrapers/sponsor_parents_scraper.py --action scrape --cache-dir my_cache
```

#### BurnSafe Scraper

```bash
# Run the main application (includes BurnSafe scraper + SMS notifications)
python src/main.py
```

### As Called Scripts (from main.py)

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

## Installation

```bash
# Install dependencies
pip install -r src/requirements.txt

# Or use the setup script
run.bat
```

## Project Structure

```text
src/
├── main.py                           # Main application entry point
├── requirements.txt                  # Python dependencies
├── scrapers/
│   ├── burnafe_scraper.py            # Nova Scotia burn restrictions
│   └── sponsor_parents_scraper.py    # Immigration sponsor parents monitoring
└── notifications/
    └── twilio_client.py              # SMS notifications via Twilio

tests/
├── test_main.py                      # Tests for main application
├── test_burnafe_scraper.py           # Tests for burn safe scraper
└── test_sponsor_scraper.py           # Tests for sponsor parents scraper

data/                                 # Cache files (created automatically)
├── sponsor_parents_cache.json        # Current website state
├── backup_sponsor_parents_cache.json # Backup cache
└── sponsor_parents_history.json      # Change history
```
