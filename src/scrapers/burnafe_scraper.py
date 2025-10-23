"""BurnSafe website scraper for Nova Scotia burn restrictions."""

from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import Optional


async def get_burn_safe_status(driver: webdriver.Chrome) -> Optional[str]:
    """
    Scrapes the Nova Scotia BurnSafe website for Halifax County burn status.
    
    Args:
        driver: Selenium WebDriver instance to use for scraping
        
    Returns:
        str | None: A human-readable burn status message, or None if unable to determine status.
        
    Raises:
        WebDriverException: If the web scraping fails.
        NoSuchElementException: If the expected page elements are not found.
    """
    driver.get('https://novascotia.ca/burnsafe/')
    burn_safe_element = driver.find_element(By.CSS_SELECTOR, 'tr#Halifax-County > td')
    burn_safe_status = burn_safe_element.get_attribute('class')
    burn_message = 'Aw... no burning today.'

    if burn_safe_status:
        if burn_safe_status == 'status-restricted':
            burn_message = 'Prep the barbie for a late burn.'
        elif burn_safe_status == 'status-burn':
            burn_message = 'Yay... early burn!'
        else:
            burn_message = 'Aw... no burning today.'

    return burn_message