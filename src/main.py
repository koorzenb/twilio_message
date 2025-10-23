from dotenv import load_dotenv
import os
import asyncio
from selenium import webdriver
from scrapers.burnafe_scraper import get_burn_safe_status
from notifications.twilio_client import TwilioSMSClient

# async def get_website_html(url: str):
#     print(f'Fetching data from {url}...')
#
#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         data = response.text
#         return BeautifulSoup(data, 'html.parser')
#     except Exception as error:
#         raise Exception(f"Error fetching data: {str(error)}")

if __name__ == "__main__":
    async def main():
        # Load environment variables
        load_dotenv()
        
        # Initialize Twilio client
        try:
            sms_client = TwilioSMSClient()
        except ValueError as e:
            print(f"Failed to initialize Twilio client: {e}")
            return
        
        # Get burn status
        messages = ''
        messages += f"BurnSafe: {await get_burn_safe_status(driver)}"
        
        # Send notification
        success = sms_client.send_notification(messages)
        if success:
            print("Notification sent successfully")
        else:
            print("Failed to send notification")

    # TODO: if uploading to PythonAnywhere, remember to adjust .env file
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    asyncio.run(main())
