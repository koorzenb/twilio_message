# Copilot Instructions for Twilio Message Project

**FOR CODING AGENTS ONLY**: These instructions are specifically designed for AI coding agents (GitHub Copilot, Claude, etc.) working on this project. Human developers should refer to the project documentation and README files.

## Project Overview
This is a Python-based automation tool that scrapes websites and sends SMS notifications via Twilio. The project focuses on web scraping, API integration, and automated messaging for important alerts and notifications.

## Python Programming Conventions

### Code Style & Formatting
- Follow **PEP 8** style guidelines strictly
- Use **4 spaces** for indentation (no tabs)
- Maximum line length of **88 characters** (Black formatter standard)
- Use **double quotes** for strings unless single quotes avoid escaping
- Add blank lines around function and class definitions
- Use meaningful variable and function names in **snake_case**
- Constants should be in **UPPER_CASE**

### Type Hints
- Always use type hints for function parameters and return values
- Use `from typing import` for complex types (List, Dict, Optional, Union)
- Example: `def get_website_status() -> str | None:`
- Use `Optional[Type]` or `Type | None` for nullable values

### Error Handling
- Use specific exception types rather than bare `except:`
- Implement proper exception handling for external API calls
- Log errors with meaningful messages
- Use context managers (`with` statements) for resource management
- Example:
```python
try:
    response = client.messages.create(...)
except TwilioException as e:
    logger.error(f"Failed to send SMS: {e}")
    raise
```

### Async/Await Patterns
- Use `async def` for I/O-bound operations (web scraping, API calls)
- Properly `await` async functions
- Use `asyncio.run()` for top-level async execution
- Handle async exceptions appropriately
- Consider using `aiohttp` for HTTP requests instead of `requests`

### Environment Variables & Configuration
- Use `python-dotenv` for environment variable management
- Never hardcode sensitive data (API keys, tokens, phone numbers)
- Validate required environment variables at startup
- Use meaningful environment variable names with project prefix
- Example: `TWILIO_MESSAGE_ACCOUNT_SID`


### Logging
- Use the `logging` module instead of `print()` statements
- Configure appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Include timestamps and context in log messages
- Example:
```python
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
```

### Testing Guidelines
- Write unit tests for all functions using `pytest`
- Mock external dependencies (Twilio API, web requests)
- Test both success and failure scenarios
- Use fixtures for common test setup
- Aim for >80% code coverage
- Example test structure:
```python
import pytest
from unittest.mock import Mock, patch

@patch('main.webdriver.Chrome')
def test_get_website_status(mock_driver):
    # Test implementation
    pass
```

### Documentation
- Use docstrings for all functions and classes (Google or NumPy style)
- Include parameter types and descriptions
- Document exceptions that may be raised
- Example:
```python
async def get_website_status() -> str | None:
    """
    Scrapes a website for status information and returns a human-readable message.
    
    Returns:
        str | None: A human-readable status message, or None if unable to determine status.
        
    Raises:
        WebDriverException: If the web scraping fails.
        NoSuchElementException: If the expected page elements are not found.
    """
```

### Dependency Management
- Pin exact versions in `requirements.txt`
- Use virtual environments for isolation
- Keep dependencies minimal and up-to-date
- Consider using `poetry` or `pipenv` for advanced dependency management
- Separate development dependencies from production dependencies

### Security Considerations
- Never commit `.env` files or credentials
- Use environment variables for all sensitive data
- Validate and sanitize any external input
- Implement rate limiting for API calls
- Use HTTPS for all external communications

### File Organization
- Keep the main execution logic in `if __name__ == "__main__":` block
- Separate concerns into different modules as the project grows
- Use meaningful file and directory names
- Consider this structure for larger projects:
```
src/
├── __init__.py
├── main.py
├── scrapers/
│   ├── __init__.py
│   └── website_scraper.py
├── notifications/
│   ├── __init__.py
│   └── twilio_client.py
└── config/
    ├── __init__.py
    └── settings.py
```

### Performance Considerations
- Use connection pooling for HTTP requests
- Implement caching for repeated API calls
- Consider using `asyncio` for concurrent operations
- Profile code to identify bottlenecks
- Use generators for large data processing

### Git & Version Control
- Write meaningful commit messages
- Use feature branches for new development
- Tag releases with semantic versioning
- Keep the repository clean (use `.gitignore`)
- Include changelog for notable changes

### Specific Project Patterns

#### Web Scraping Pattern
```python
async def scrape_website_data(url: str, selector: str) -> str | None:
    """Generic web scraping function with error handling."""
    try:
        driver.get(url)
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element.get_attribute('class')
    except (NoSuchElementException, TimeoutException) as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return None
    finally:
        # Cleanup if needed
        pass
```

#### Notification Pattern
```python
def send_notification(message: str, recipient: str) -> bool:
    """Send notification with proper error handling and logging."""
    try:
        # Send message logic
        logger.info(f"Notification sent successfully to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False
```

### Code Review Checklist
- [ ] Type hints are present and accurate
- [ ] Error handling is comprehensive
- [ ] No hardcoded secrets or credentials
- [ ] Async/await is used correctly
- [ ] WebDriver resources are properly managed
- [ ] Tests are written and passing
- [ ] Documentation is complete and accurate
- [ ] Dependencies are pinned and minimal
- [ ] Code follows PEP 8 standards
- [ ] Logging is appropriate and informative

### Development Tools
- Use `black` for code formatting
- Use `flake8` or `ruff` for linting
- Use `mypy` for type checking
- Use `pytest` for testing
- Use `pre-commit` hooks for automated checks
- Consider using `GitHub Actions` for CI/CD

## Project-Specific Guidelines

### Website Scraping
- Always check for website structure changes
- Implement fallback parsing strategies
- Cache status to avoid unnecessary requests
- Handle different status types explicitly
- Use appropriate selectors for target websites

### Twilio Integration
- Always verify phone numbers before deployment
- Implement retry logic for failed messages
- Monitor Twilio usage and costs
- Use test credentials for development

### Deployment Considerations
- Ensure ChromeDriver compatibility on target platform
- Set up environment variables securely
- Consider scheduling (cron jobs, task schedulers)
- Implement health checks and monitoring

Remember: This project handles real-world notifications that may affect user decisions. Prioritize reliability, error handling, and thorough testing.