"""Email client for sending notifications via SMTP."""

import smtplib
import ssl
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import os
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Configuration for email client."""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    sender_email: str
    sender_name: Optional[str] = None
    use_tls: bool = True
    use_ssl: bool = False


@dataclass
class EmailMessage:
    """Email message structure."""
    to_emails: List[str]
    subject: str
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    cc_emails: Optional[List[str]] = None
    bcc_emails: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    reply_to: Optional[str] = None


class EmailSMTPClient:
    """
    Professional email client with SMTP support, retry logic, and error handling.
    
    Supports multiple email providers (Gmail, Outlook, custom SMTP servers)
    with SSL/TLS encryption and comprehensive error handling.
    """
    
    # Common SMTP server configurations
    SMTP_CONFIGS = {
        'gmail': {'server': 'smtp.gmail.com', 'port': 587, 'use_tls': True},
        'outlook': {'server': 'smtp-mail.outlook.com', 'port': 587, 'use_tls': True},
        'yahoo': {'server': 'smtp.mail.yahoo.com', 'port': 587, 'use_tls': True},
        'icloud': {'server': 'smtp.mail.me.com', 'port': 587, 'use_tls': True},
    }
    
    def __init__(self, config: Optional[EmailConfig] = None):
        """
        Initialize the email client.
        
        Args:
            config: Email configuration. If None, will load from environment variables.
            
        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        if config:
            self.config = config
        else:
            self.config = self._load_config_from_env()
        
        self._validate_config()
        logger.info(f"Email client initialized for {self.config.smtp_server}:{self.config.smtp_port}")
    
    def _load_config_from_env(self) -> EmailConfig:
        """Load email configuration from environment variables."""
        # Check for provider shortcut first
        provider = os.getenv('EMAIL_PROVIDER', '').lower()
        
        if provider in self.SMTP_CONFIGS:
            smtp_config = self.SMTP_CONFIGS[provider]
            smtp_server = smtp_config['server']
            smtp_port = smtp_config['port']
            use_tls = smtp_config.get('use_tls', True)
        else:
            # Use custom SMTP settings
            smtp_server = os.getenv('SMTP_HOST', '')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        return EmailConfig(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=os.getenv('EMAIL_USERNAME', ''),
            password=os.getenv('EMAIL_PASSWORD', ''),
            sender_email=os.getenv('SENDER_EMAIL', ''),
            sender_name=os.getenv('SENDER_NAME', 'Website Monitor'),
            use_tls=use_tls,
            use_ssl=os.getenv('SMTP_USE_SSL', 'false').lower() == 'true'
        )
    
    def _validate_config(self) -> None:
        """Validate email configuration."""
        required_fields = ['smtp_server', 'smtp_port', 'username', 'password', 'sender_email']
        missing_fields = []
        
        for field in required_fields:
            if not getattr(self.config, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required email configuration: {', '.join(missing_fields)}")
        
        if not (1 <= self.config.smtp_port <= 65535):
            raise ValueError(f"Invalid SMTP port: {self.config.smtp_port}")
        
        if '@' not in self.config.sender_email:
            raise ValueError(f"Invalid sender email format: {self.config.sender_email}")
    
    def send_email(
        self, 
        message: EmailMessage, 
        max_retries: int = 3, 
        retry_delay: float = 2.0
    ) -> bool:
        """
        Send an email with retry logic.
        
        Args:
            message: Email message to send
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not message.to_emails:
            logger.error("No recipient emails provided")
            return False
        
        # Validate email addresses
        invalid_emails = [email for email in message.to_emails if '@' not in email]
        if invalid_emails:
            logger.error(f"Invalid email addresses: {invalid_emails}")
            return False
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Sending email attempt {attempt + 1}/{max_retries}")
                self._send_email_internal(message)
                logger.info(f"Email sent successfully to {len(message.to_emails)} recipients")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                last_exception = e
                logger.error(f"SMTP Authentication failed: {e}")
                # Don't retry authentication errors
                break
                
            except smtplib.SMTPRecipientsRefused as e:
                last_exception = e
                logger.error(f"Recipients refused: {e}")
                # Don't retry if all recipients are invalid
                break
                
            except (smtplib.SMTPException, ssl.SSLError, ConnectionError) as e:
                last_exception = e
                logger.warning(f"Email send attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                break
        
        logger.error(f"Failed to send email after {max_retries} attempts: {last_exception}")
        return False
    
    def _send_email_internal(self, message: EmailMessage) -> None:
        """Internal method to send email via SMTP."""
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = message.subject
        msg['From'] = f"{self.config.sender_name} <{self.config.sender_email}>" if self.config.sender_name else self.config.sender_email
        msg['To'] = ', '.join(message.to_emails)
        
        if message.cc_emails:
            msg['Cc'] = ', '.join(message.cc_emails)
        
        if message.reply_to:
            msg['Reply-To'] = message.reply_to
        
        # Add text body
        if message.text_body:
            text_part = MIMEText(message.text_body, 'plain', 'utf-8')
            msg.attach(text_part)
        
        # Add HTML body
        if message.html_body:
            html_part = MIMEText(message.html_body, 'html', 'utf-8')
            msg.attach(html_part)
        
        # Add attachments
        if message.attachments:
            for file_path in message.attachments:
                if os.path.exists(file_path):
                    self._add_attachment(msg, file_path)
                else:
                    logger.warning(f"Attachment file not found: {file_path}")
        
        # Send email
        all_recipients = message.to_emails.copy()
        if message.cc_emails:
            all_recipients.extend(message.cc_emails)
        if message.bcc_emails:
            all_recipients.extend(message.bcc_emails)
        
        # Connect and send
        if self.config.use_ssl:
            # Use SSL connection (port 465 typically)
            with smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port) as server:
                server.login(self.config.username, self.config.password)
                server.send_message(msg, to_addrs=all_recipients)
        else:
            # Use regular SMTP with optional TLS (port 587 typically)
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls(context=ssl.create_default_context())
                server.login(self.config.username, self.config.password)
                server.send_message(msg, to_addrs=all_recipients)
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str) -> None:
        """Add file attachment to email message."""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = Path(file_path).name
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            logger.info(f"Added attachment: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to add attachment {file_path}: {e}")
    
    def send_notification(
        self, 
        to_emails: List[str], 
        subject: str, 
        body: str, 
        is_html: bool = False,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Convenience method for sending simple notifications.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML formatted
            attachments: Optional list of file paths to attach
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        message = EmailMessage(
            to_emails=to_emails,
            subject=subject,
            html_body=body if is_html else None,
            text_body=body if not is_html else None,
            attachments=attachments
        )
        
        return self.send_email(message)
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection and authentication.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info("Testing SMTP connection...")
            
            if self.config.use_ssl:
                with smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port) as server:
                    server.login(self.config.username, self.config.password)
            else:
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                    if self.config.use_tls:
                        server.starttls(context=ssl.create_default_context())
                    server.login(self.config.username, self.config.password)
            
            logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False


def create_email_client_from_env() -> EmailSMTPClient:
    """
    Convenience function to create email client from environment variables.
    
    Returns:
        EmailSMTPClient: Configured email client
        
    Raises:
        ValueError: If required environment variables are missing
    """
    return EmailSMTPClient()


def send_simple_email(to_emails: List[str], subject: str, body: str, is_html: bool = False) -> bool:
    """
    Convenience function to send a simple email using environment configuration.
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject
        body: Email body content
        is_html: Whether the body is HTML formatted
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        client = create_email_client_from_env()
        return client.send_notification(to_emails, subject, body, is_html)
    except Exception as e:
        logger.error(f"Failed to send simple email: {e}")
        return False


if __name__ == "__main__":
    """Test the email client when run as a standalone script."""
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create email client
        print("Creating email client...")
        client = create_email_client_from_env()
        
        # Test connection
        print("Testing SMTP connection...")
        if client.test_connection():
            print("✅ SMTP connection successful!")
        else:
            print("❌ SMTP connection failed!")
            sys.exit(1)
        
        # Test email (if recipient specified)
        test_recipient = os.getenv('TEST_EMAIL_RECIPIENT')
        if test_recipient:
            print(f"Sending test email to {test_recipient}...")
            success = client.send_notification(
                to_emails=[test_recipient],
                subject="IRCC Monitor - Email Client Test",
                body="This is a test email from the IRCC Website Monitor email client.\n\nIf you receive this, the email configuration is working correctly!",
                is_html=False
            )
            
            if success:
                print("✅ Test email sent successfully!")
            else:
                print("❌ Test email failed!")
                sys.exit(1)
        else:
            print("ℹ️  Set TEST_EMAIL_RECIPIENT environment variable to send a test email")
        
        print("Email client test completed successfully!")
        
    except Exception as e:
        print(f"❌ Email client test failed: {e}")
        sys.exit(1)