# Product Requirements Document (PRD)

# Twilio Message - Website Monitoring & SMS Notification System

**Version:** 2.0  
**Date:** October 23, 2025  
**Status:** Active Development

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Overview](#product-overview)
3. [Architecture](#architecture)
4. [Technical Specifications](#technical-specifications)
5. [Available Scrapers](#available-scrapers)
6. [Development Guidelines](#development-guidelines)
7. [Installation & Setup](#installation--setup)
8. [Project Structure](#project-structure)
9. [Environment Configuration](#environment-configuration)
10. [Testing Strategy](#testing-strategy)
11. [Future Roadmap](#future-roadmap)

## Executive Summary

Twilio Message is a Python-based website monitoring system that automatically detects changes on websites and sends SMS notifications via Twilio. The system has evolved from a single-purpose scraper to a **generic, extensible architecture** that allows rapid development of new website scrapers.

### Key Features

- **Generic Base Class Architecture**: Reusable `BaseWebsiteScraper` for any website
- **Multiple Scraper Support**: Currently monitors Nova Scotia BurnSafe and Canada.ca Sponsor Parents pages
- **Intelligent Change Detection**: Monitors specific content elements rather than entire pages
- **Persistent Caching**: Backup mechanisms and change history tracking
- **SMS Notifications**: Twilio integration with retry logic
- **Standalone & Module Usage**: Can be run as scripts or imported as modules

## Product Overview

### Primary Use Cases

1. **Government Website Monitoring**: Track updates to immigration, permit, and regulatory websites
2. **News & Alert Monitoring**: Monitor news sites for breaking updates
3. **Service Status Monitoring**: Track service availability and status changes
4. **Generic Website Monitoring**: Monitor any website for content changes

### Target Users

- **Developers**: Need to monitor API documentation or service status pages
- **Immigrants**: Tracking government immigration website updates
- **Citizens**: Monitoring permit applications, burn restrictions, etc.
- **Businesses**: Tracking competitor or regulatory websites

## Architecture

The system uses a **generic base class pattern** that provides common functionality while allowing site-specific customization.

### Core Components

#### 1. BaseWebsiteScraper (Generic Base Class)

**Purpose**: Provides common website scraping functionality  
**Location**: `src/scrapers/base_website_scraper.py`

**Features**:

- HTTP requests with retry logic and custom headers
- Intelligent caching system with backup mechanism
- Change detection comparing current vs cached data
- Historical change tracking with timestamps
- Comprehensive error handling and logging
- Support for concurrent scraping operations

**Abstract Methods** (must be implemented by subclasses):

```python
def _extract_target_content(self, soup: BeautifulSoup) -> str
def _extract_title(self, soup: BeautifulSoup) -> str  
def _extract_main_content(self, soup: BeautifulSoup) -> str
def _extract_important_notices(self, soup: BeautifulSoup) -> List[str]
```

**Optional Methods** (can be overridden):

```python
def _extract_last_updated(self, soup: BeautifulSoup) -> Optional[str]
def _extract_additional_data(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]
def _detect_additional_changes(self, current_data: Dict, cached_data: Dict) -> Optional[str]
```

#### 2. Site-Specific Scrapers

Each scraper inherits from `BaseWebsiteScraper` and implements only the site-specific logic:

- **SponsorParentsScraper**: Canada.ca immigration website
- **BurnSafeScraper**: Nova Scotia burn restrictions (legacy Selenium-based)
- **ExampleWebsiteScraper**: Generic template for new websites

#### 3. Notification System

**TwilioSMSClient**: Professional SMS client with:

- Exponential backoff retry logic
- Phone number validation
- Error handling and logging
- Rate limiting considerations

## Technical Specifications

### Dependencies

```
python-dotenv==1.0.0    # Environment variable management
twilio==9.6.3           # SMS notifications
selenium==4.33.0        # Web automation (legacy scrapers)
requests==2.31.0        # HTTP requests
beautifulsoup4==4.12.2  # HTML parsing
```

### Supported Python Versions

- **Primary**: Python 3.11+
- **Tested**: Python 3.9+
- **Minimum**: Python 3.8+

### Performance Characteristics

- **Response Time**: < 5 seconds for typical web scraping
- **Retry Logic**: 3 attempts with exponential backoff
- **Cache Performance**: File-based JSON storage with backup
- **Memory Usage**: < 50MB for typical operation
- **Concurrent Support**: Thread-safe design

### Security Features

- **No Hardcoded Credentials**: All sensitive data via environment variables
- **Input Validation**: Sanitization of external data
- **HTTPS Only**: All external communications encrypted
- **Rate Limiting**: Respectful scraping practices

## Available Scrapers

### 1. Sponsor Parents Scraper (Production Ready)

**Website**: `https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/family-sponsorship/sponsor-parents-grandparents.html`

**Monitoring Strategy**:

- **Target Content**: `gcds-date-modified` element (Government of Canada Design System)
- **Change Detection**: Hash-based comparison of date-modified content
- **Fallback Strategy**: Multiple CSS selectors for robustness

**Usage**:

```python
from scrapers.sponsor_parents_scraper import SponsorParentsScraper

scraper = SponsorParentsScraper()
data = scraper.scrape_website_data()
has_updates = scraper.check_for_updates()
```

### 2. BurnSafe Scraper (Legacy - Selenium)

**Website**: Nova Scotia BurnSafe burn restriction status

**Technology**: Selenium WebDriver (scheduled for migration to BeautifulSoup in Phase 1.4)

**Integration**: Works with main application for SMS notifications

### 3. Example Scraper (Template)

**Purpose**: Demonstrates how to create scrapers for any website

**Flexibility**: Parameterized target selectors and notice patterns

**Usage Examples**:

```python
# News website
scraper = create_news_scraper("https://example-news.com")

# Blog monitoring  
scraper = create_blog_scraper("https://example-blog.com")

# Generic website
scraper = create_generic_scraper("https://any-site.com", ".main-content")
```

## Development Guidelines

### Creating a New Scraper

1. **Inherit from BaseWebsiteScraper**:

```python
class YourScraper(BaseWebsiteScraper):
    def __init__(self):
        super().__init__(
            base_url="https://your-site.com",
            cache_file="your_cache.json",
            history_file="your_history.json"
        )
```

2. **Implement Required Abstract Methods**:

```python
def _extract_target_content(self, soup: BeautifulSoup) -> str:
    # Return the specific content to monitor for changes
    
def _extract_title(self, soup: BeautifulSoup) -> str:
    # Return the page title
    
def _extract_main_content(self, soup: BeautifulSoup) -> str:
    # Return main page content (up to 1000 chars)
    
def _extract_important_notices(self, soup: BeautifulSoup) -> List[str]:
    # Return list of important notices/alerts
```

3. **Optional Customizations**:

- Override `_extract_last_updated()` for site-specific date patterns
- Override `_detect_additional_changes()` for custom change detection
- Override `_extract_additional_data()` for extra data collection

### Code Quality Standards

- **Type Hints**: All functions must have type annotations
- **Error Handling**: Comprehensive exception handling with logging
- **Documentation**: Google/NumPy style docstrings
- **Testing**: Unit tests with >80% coverage
- **Logging**: Structured logging with appropriate levels

### Performance Guidelines

- **Target Selectors**: Use specific CSS selectors to minimize parsing
- **Content Limits**: Limit extracted content to reasonable sizes (1000 chars for main content)
- **Caching Strategy**: Use file-based caching with backup mechanism
- **Rate Limiting**: Implement delays between requests for respectful scraping

## Installation & Setup

### Prerequisites

1. **Python 3.8+** installed
2. **Twilio Account** with phone number
3. **Environment Variables** configured

### Installation Steps

```bash
# Clone repository
git clone https://github.com/koorzenb/twilio_message.git
cd twilio_message

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r src/requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Twilio credentials
```

### Quick Start

```bash
# Test sponsor parents scraper
python src/scrapers/sponsor_parents_scraper.py --action scrape

# Run main application (BurnSafe + SMS)
python src/main.py
```

## Project Structure

```text
twilio_message/
├── src/
│   ├── main.py                           # Main application entry point
│   ├── requirements.txt                  # Python dependencies
│   ├── scrapers/
│   │   ├── base_website_scraper.py       # Generic base class ⭐
│   │   ├── burnafe_scraper.py            # Nova Scotia burn restrictions
│   │   ├── sponsor_parents_scraper.py    # Immigration monitoring ⭐
│   │   └── example_scraper.py            # Template for new scrapers ⭐
│   └── notifications/
│       └── twilio_client.py              # SMS notifications
├── tests/
│   ├── test_main.py                      # Main application tests
│   ├── test_burnafe_scraper.py           # BurnSafe scraper tests
│   └── test_sponsor_scraper.py           # Sponsor scraper tests
├── data/                                 # Cache files (auto-created)
│   ├── sponsor_parents_cache.json        # Current website state
│   ├── backup_sponsor_parents_cache.json # Backup cache
│   └── sponsor_parents_history.json      # Change history
├── .env                                  # Environment variables
├── run.bat                               # Windows setup script
├── README.md                             # User documentation
├── PRD.md                                # This document
└── PLAN.md                               # Development roadmap
```

⭐ = **New generic architecture components**

## Environment Configuration

### Required Variables

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token  
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Notification Settings
MY_PHONE_NUMBER=your_recipient_phone_number
```

### Optional Variables

```env
# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT='%(asctime)s - %(levelname)s - %(message)s'

# Cache Configuration  
CACHE_DIR=data
MAX_HISTORY_ENTRIES=100

# Request Configuration
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

## Testing Strategy

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Multi-component interaction testing
3. **End-to-End Tests**: Full workflow testing
4. **Mock Tests**: External dependency mocking

### Test Files

- **`test_main.py`**: Main application and Twilio client tests
- **`test_burnafe_scraper.py`**: BurnSafe scraper tests (requires ChromeDriver)
- **`test_sponsor_scraper.py`**: Sponsor Parents scraper tests with caching
- **`test_base_scraper.py`**: Generic base class tests (future)

### Running Tests

```bash
# All tests
python -m pytest tests/

# Individual test files  
python tests/test_sponsor_scraper.py

# With coverage
python -m pytest tests/ --cov=src/
```

## Future Roadmap

### Phase 1: Foundation (Current)

- ✅ Generic base class architecture
- ✅ Sponsor Parents scraper migration
- ✅ Enhanced caching system
- ✅ Standalone script capability

### Phase 2: Migration & Enhancement

- 🔄 **Phase 1.4**: Migrate BurnSafe scraper from Selenium to BeautifulSoup
- 📋 **Phase 1.5**: Add comprehensive unit tests for base class
- 📋 **Phase 1.6**: Implement async/await pattern for better performance

### Phase 3: Advanced Features

- 📋 **Multi-website monitoring**: Single application monitoring multiple sites
- 📋 **Email notifications**: Alternative to SMS
- 📋 **Web dashboard**: Browser-based monitoring interface
- 📋 **Scheduling system**: Cron-like scheduling for automated monitoring

### Phase 4: Enterprise Features

- 📋 **Database storage**: Replace file-based caching
- 📋 **API endpoints**: REST API for monitoring control
- 📋 **Multi-user support**: User accounts and permissions
- 📋 **Cloud deployment**: Docker containerization and cloud hosting

## Success Metrics

### Technical Metrics

- **Code Reuse**: >80% of scraper functionality provided by base class
- **Development Speed**: New scrapers created in <30 minutes
- **Reliability**: >99% uptime for monitoring services
- **Performance**: <5 second response time for scraping operations

### User Metrics

- **Notification Accuracy**: >95% true positive rate for change detection
- **False Positives**: <5% false positive rate
- **User Satisfaction**: Positive feedback from government website monitoring

---

**Document Owner**: Development Team  
**Last Updated**: October 23, 2025  
**Next Review**: November 15, 2025
