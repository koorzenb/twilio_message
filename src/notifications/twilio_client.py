"""Twilio SMS client for sending notifications."""

import os
import time
import logging
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)


class TwilioSMSClient:
    """
    A client for sending SMS messages via Twilio API with error handling and retry logic.
    """
    
    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None, 
                 from_number: Optional[str] = None):
        """
        Initialize the Twilio SMS client.
        
        Args:
            account_sid: Twilio account SID (if None, will read from TWILIO_ACCOUNT_SID env var)
            auth_token: Twilio auth token (if None, will read from TWILIO_AUTH_TOKEN env var)
            from_number: Twilio phone number to send from (if None, will read from TWILIO_PHONE_NUMBER env var)
            
        Raises:
            ValueError: If required credentials are not provided
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Missing required Twilio credentials. Please provide account_sid, auth_token, and from_number")
        
        self.client = Client(self.account_sid, self.auth_token)
        logger.info("Twilio SMS client initialized successfully")
    
    def send_message(self, message: str, to_number: str, max_retries: int = 3, 
                    retry_delay: float = 1.0) -> Dict[str, Any]:
        """
        Send an SMS message with retry logic.
        
        Args:
            message: The message content to send
            to_number: The recipient's phone number
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
            
        Returns:
            Dict containing success status and message details or error information
            
        Raises:
            TwilioException: If all retry attempts fail
        """
        if not message.strip():
            raise ValueError("Message content cannot be empty")
        
        if not to_number.strip():
            raise ValueError("Recipient phone number cannot be empty")
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Sending SMS to {to_number} (attempt {attempt + 1}/{max_retries + 1})")
                
                twilio_message = self.client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=to_number
                )
                
                logger.info(f"SMS sent successfully. Message SID: {twilio_message.sid}")
                
                return {
                    'success': True,
                    'message_sid': twilio_message.sid,
                    'status': twilio_message.status,
                    'attempt': attempt + 1
                }
                
            except TwilioException as e:
                last_exception = e
                logger.warning(f"Twilio API error on attempt {attempt + 1}: {e}")
                
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
        
        # If we get here, all attempts failed
        error_msg = f"Failed to send SMS after {max_retries + 1} attempts: {last_exception}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'error': str(last_exception),
            'attempts': max_retries + 1
        }
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Basic validation for phone numbers.
        
        Args:
            phone_number: The phone number to validate
            
        Returns:
            bool: True if the phone number appears valid, False otherwise
        """
        if not phone_number:
            return False
        
        # Remove common formatting characters
        cleaned = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
        
        # Check if it's all digits and has reasonable length
        if not cleaned.isdigit():
            return False
        
        # Most phone numbers are between 10-15 digits
        return 10 <= len(cleaned) <= 15
    
    def send_notification(self, message: str, recipient: Optional[str] = None) -> bool:
        """
        Convenience method to send a notification with default recipient.
        
        Args:
            message: The message content to send
            recipient: The recipient's phone number (if None, uses MY_PHONE_NUMBER env var)
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        to_number = recipient or os.getenv('MY_PHONE_NUMBER')
        
        if not to_number:
            logger.error("No recipient phone number provided and MY_PHONE_NUMBER env var not set")
            return False
        
        if not self.validate_phone_number(to_number):
            logger.error(f"Invalid phone number format: {to_number}")
            return False
        
        try:
            result = self.send_message(message, to_number)
            return result['success']
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False