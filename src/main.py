from dotenv import load_dotenv
import os
import logging
from typing import List
from scrapers.scraper import Scraper
from notifications.email_client import EmailSMTPClient, EmailMessage
from notifications.email_templates import EmailTemplateRenderer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _get_email_recipients() -> List[str]:
    """
    Get email recipients from environment variables.
    
    Returns:
        List[str]: List of recipient email addresses
    """
    recipients = []
    
    # Primary recipient
    primary_email = os.getenv('RECIPIENT_EMAIL')
    if primary_email:
        recipients.append(primary_email)
    
    # Additional recipients (comma-separated)
    additional_emails = os.getenv('ADDITIONAL_RECIPIENTS', '')
    if additional_emails:
        additional_list = [email.strip() for email in additional_emails.split(',') if email.strip()]
        recipients.extend(additional_list)
    
    return recipients

def _scrape_data(scraper: Scraper, provider: str, recipients: List[str]) -> bool:
    try:
        # Scrape the sponsor parents website data
        logger.info("Starting website scraping check...")
        scraped_data = scraper.scrape_website_data()
        
        if scraped_data is None:
            logger.error(f"Failed to scrape {provider} website data")
            return False
        
        # Check for updates using the scraped data
        has_updates = scraper.check_for_updates(scraped_data)
        
        # Get email recipients
        if not recipients:
            logger.error("No email recipients configured. Please set RECIPIENT_EMAIL environment variable.")
            return False
        
        # Generate email content
        logger.info("Generating email content...")
        
        renderer = EmailTemplateRenderer()
        html_content = renderer.render_update_notification(scraped_data, has_updates, provider, "html")

        
        # Determine email subject
        if has_updates:
            subject = f"🚨 {provider} Website Update Detected - Action Required"
        else:
            subject = f"✅ {provider} Website Status Check - No Changes"
        
        # Create email message
        #  only email to first recipient for xbox
        
        email_message = EmailMessage(
            to_emails=recipients,
            subject=subject,
            html_body=html_content,
            reply_to=os.getenv('SENDER_EMAIL')
        )
        
        # Initialize email client and send
        logger.info("Initializing email client...")
        email_client = EmailSMTPClient()
        
        logger.info(f"Sending notification to {len(recipients)} recipients...")
        success = email_client.send_email(email_message)
        
        if success:
            status = "UPDATES DETECTED" if has_updates else "NO UPDATES"
            logger.info(f"Email notification sent successfully! Status: {status}")
            logger.info(f"Recipients: {', '.join(recipients)}")
            logger.info(f"Subject: {subject}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending email notification: {e}")
        return False
    
def send_email_update() -> bool:
    """
    Send email notification with website scraping update information.
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # only send on Fridays
    recipients = _get_email_recipients()
    from datetime import datetime
    if datetime.now().weekday() == 4:  # 4 corresponds to Friday
        ircc_scraper = Scraper(base_url="https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/family-sponsorship/sponsor-parents-grandparents.html", target_element='body > main > section > gcds-date-modified', history_file="sponsor_parents_history.json", cache_file="sponsor_parents_cache.json", use_selenium=True)
        return _scrape_data(scraper=ircc_scraper, provider="IRCC", recipients=[recipients[0], recipients[1]])
    # else:
    #     display_monitor_scraper = Scraper(base_url="https://www.walmart.ca/en/ip/LG-27-FHD-IPS-3-Side-Borderless-Monitor-with-AMD/1457XYBFE7ZU", target_element='span.b.lh-copy.dark-gray.f1.mr2 > span.inline-flex.flex-column > span', history_file="display_history.json", cache_file="display_cache.json")
    #     return _scrape_data(scraper=display_monitor_scraper, provider="Walmart", recipients=[recipients[0]])
    return False
    
if __name__ == "__main__":
    def main():
        """Main application entry point."""
        # Load environment variables
        load_dotenv()
        
        logger.info("=== Website Monitors Started ===")
        
        # Validate email configuration
        try:
            recipients = _get_email_recipients()
            if not recipients:
                print("❌ Error: No email recipients configured!")
                print("Please set RECIPIENT_EMAIL environment variable.")
                logger.error("No email recipients configured")
                return
                
            logger.info(f"Email recipients configured: {len(recipients)}")
            
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            logger.error(f"Configuration error: {e}")
            return
        
        # Send email notification
        try:
            success = send_email_update()
            
            if success:
                print("✅ Email notification sent successfully!")
                logger.info("=== Website Monitor Completed Successfully ===")
            else:
                print("❌ Failed to send email notification")
                logger.error("=== Website Monitor Failed ===")
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            logger.error(f"Unexpected error in main: {e}")
            logger.error("=== Website Monitor Failed ===")

    main()
