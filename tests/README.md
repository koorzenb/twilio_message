# Tests Directory

This directory contains test scripts for the Twilio Message project.

## Test Files

- **`test_main.py`** - Tests for the main application components and Twilio client
- **`test_burnafe_scraper.py`** - Tests for the Nova Scotia BurnSafe website scraper
- **`test_sponsor_scraper.py`** - Tests for the Sponsor Parents website scraper with persistent caching

## Running Tests

From the project root directory:

```bash
# Run all tests
python -m pytest tests/

# Run individual test files
python tests/test_main.py
python tests/test_burnafe_scraper.py
python tests/test_sponsor_scraper.py
```

From the tests directory:

```bash
cd tests
python test_main.py
python test_burnafe_scraper.py
python test_sponsor_scraper.py
```

## Requirements

Make sure you have installed all dependencies:

```bash
pip install -r src/requirements.txt
```

## Notes

- Some tests may require environment variables (Twilio credentials) to be set
- The BurnSafe scraper test requires Chrome/ChromeDriver (will be migrated to BeautifulSoup in Phase 1.4)
- The Sponsor Parents scraper test will create cache files in a `data/` directory
