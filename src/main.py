from dotenv import load_dotenv
import os
from twilio.rest import Client
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
from scrapers.burnafe_scraper import get_burn_safe_status

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
    def send_messages(messages):
        global driver
        load_dotenv()
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=messages,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=os.getenv('MY_PHONE_NUMBER') or '123',  # must be a verified number in your twilio account
        )

    async def main():
        messages = ''
        messages += f"BurnSafe: {await get_burn_safe_status(driver)}"
        send_messages(messages)

    # TODO: if uploading to PythonAnywhere, remember to adjust .env file
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    asyncio.run(main())
