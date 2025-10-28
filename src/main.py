from dotenv import load_dotenv
import os
import logging
from typing import List
from scrapers.sponsor_parents_scraper import scrape_sponsor_parents_data, check_sponsor_parents_updates, SponsorParentsScraper
from notifications.email_client import EmailSMTPClient, EmailMessage
from notifications.email_templates import render_ircc_html_email, render_ircc_text_email

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

def _send_email_notification() -> bool:
    """
    Send email notification with IRCC website update information.
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Scrape the sponsor parents website data
        logger.info("Starting IRCC website monitoring check...")
        scraped_data = scrape_sponsor_parents_data()
        
        if scraped_data is None:
            logger.error("Failed to scrape IRCC website data")
            return False
        
        # Check for updates using the scraped data
        has_updates = check_sponsor_parents_updates(scraped_data)
        
        # Get recent history if updates detected
        recent_history = None
        if has_updates:
            scraper = SponsorParentsScraper()
            recent_history = scraper.get_change_history(5)
        
        # Get email recipients
        recipients = _get_email_recipients()
        if not recipients:
            logger.error("No email recipients configured. Please set RECIPIENT_EMAIL environment variable.")
            return False
        
        # Generate email content
        logger.info("Generating email content...")
        html_content = render_ircc_html_email(scraped_data, has_updates, recent_history)
        text_content = render_ircc_text_email(scraped_data, has_updates, recent_history)
        
        # Determine email subject
        if has_updates:
            subject = "🚨 IRCC Website Update Detected - Action Required"
        else:
            subject = "✅ IRCC Website Status Check - No Changes"
        
        # Create email message
        email_message = EmailMessage(
            to_emails=recipients,
            subject=subject,
            html_body=html_content,
            text_body=text_content,
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


if __name__ == "__main__":
    def main():
        """Main application entry point."""
        # Load environment variables
        load_dotenv()
        
        logger.info("=== IRCC Website Monitor Started ===")
        
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
            success = _send_email_notification()
            
            if success:
                print("✅ Email notification sent successfully!")
                logger.info("=== IRCC Website Monitor Completed Successfully ===")
            else:
                print("❌ Failed to send email notification")
                logger.error("=== IRCC Website Monitor Failed ===")
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            logger.error(f"Unexpected error in main: {e}")
            logger.error("=== IRCC Website Monitor Failed ===")

    main()
