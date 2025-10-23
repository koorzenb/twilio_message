"""Test script for the main application."""

import sys
import os
# Add the src directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from notifications.twilio_client import TwilioSMSClient

def test_twilio_client():
    """Test the Twilio SMS client."""
    print("Testing Twilio SMS Client...")
    
    try:
        # Test client initialization (will fail without proper env vars, which is expected)
        print("📱 Initializing Twilio client...")
        client = TwilioSMSClient()
        print("✅ Twilio client initialized successfully")
        
        # Test phone number validation
        print("\n📞 Testing phone number validation...")
        test_numbers = [
            "+1234567890",
            "123-456-7890", 
            "(123) 456-7890",
            "invalid",
            "",
            "12345678901234567890"  # too long
        ]
        
        for number in test_numbers:
            is_valid = client.validate_phone_number(number)
            print(f"  {number:20} -> {'✅ Valid' if is_valid else '❌ Invalid'}")
            
    except ValueError as e:
        print(f"⚠️  Expected error (missing credentials): {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_application_structure():
    """Test that all required modules can be imported."""
    print("\nTesting Application Structure...")
    
    try:
        # Test imports
        modules_to_test = [
            ("scrapers.burnafe_scraper", "get_burn_safe_status"),
            ("scrapers.sponsor_parents_scraper", "SponsorParentsScraper"),
            ("notifications.twilio_client", "TwilioSMSClient"),
        ]
        
        for module_name, class_or_function in modules_to_test:
            try:
                module = __import__(module_name, fromlist=[class_or_function])
                getattr(module, class_or_function)
                print(f"✅ {module_name}.{class_or_function}")
            except ImportError as e:
                print(f"❌ {module_name}.{class_or_function}: {e}")
                
    except Exception as e:
        print(f"❌ Error testing structure: {e}")

if __name__ == "__main__":
    test_twilio_client()
    test_application_structure()