from dotenv import load_dotenv
import os
import logging
from scrapers.sponsor_parents_scraper import scrape_sponsor_parents_data, check_sponsor_parents_updates
from notifications.twilio_client import TwilioSMSClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _build_message() -> str:
    """
    Build a message containing IRCC website update information.
    
    Returns:
        str: Formatted message with update status and scraped data
    """
    try:
        # Scrape the sponsor parents website data
        scraped_data = scrape_sponsor_parents_data()
        
        if scraped_data is None:
            return "Error: Failed to scrape IRCC website data"
        
        # Create scraper instance and check for updates using the scraped data
        has_updates = check_sponsor_parents_updates(scraped_data)
        
        # Format the scraped data for display
        last_updated = scraped_data.get('last_updated', 'N/A')
        
        # Build the message
        message = f"""Did IRCC website update: {has_updates}
        - Last updated: {last_updated}"""
        
        logger.info(f"Message built successfully. Updates detected: {has_updates}")
        return message
        
    except Exception as e:
        error_msg = f"Error building message: {e}"
        logger.error(error_msg)
        return error_msg


if __name__ == "__main__":
    def main():
        # Load environment variables
        load_dotenv()
        
        # Initialize Twilio client
        try:
            sms_client = TwilioSMSClient()
        except ValueError as e:
            print(f"Failed to initialize Twilio client: {e}")
            logger.error(f"Failed to initialize Twilio client: {e}")
            return
        
        # Build message with IRCC website data
        message = _build_message()
        
        # Send notification
        success = sms_client.send_notification(message)
        if success:
            print("Notification sent successfully")
            logger.info("Notification sent successfully")
        else:
            print("Failed to send notification")
            logger.error("Failed to send notification")

    main()
