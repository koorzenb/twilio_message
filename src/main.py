import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from twilio.rest import Client
import asyncio

async def get_website_html(url: str):
    print(f'Fetching data from {url}...')

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.text
        return BeautifulSoup(data, 'html.parser')
    except Exception as error:
        raise Exception(f"Error fetching data: {str(error)}")

async def get_burn_safe_status() -> str | None:
    try:
        soup = await get_website_html('https://novascotia.ca/burnsafe/')
        burn_safe_element = soup.select_one('tr#Halifax-County > td')
        burn_safe_status = burn_safe_element.get('class')[0] if burn_safe_element and burn_safe_element.get(
            'class') else None
        print(f"BurnSafe Status: {burn_safe_status}")
    except Exception as error:
        burn_safe_status = None
        print(f"Error: {str(error)}")
    burn_message = 'Aw... no burning today.'

    if burn_safe_status:
        if burn_safe_status == 'status-restricted':
            burn_message = 'Prep the barbie for a late burn.'
        elif burn_safe_status == 'status-burn':
            burn_message = 'Yay... early burn!'
        else:
            burn_message = 'Aw... no burning today.'

    return burn_message

if __name__ == "__main__":
    def send_messages(messages):
        load_dotenv()
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=messages,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=os.getenv('MY_PHONE_NUMBER'),  # must be a verified number in your twilio account
        )

        print(message)

    async def main():
        messages = ''
        messages += f"BurnSafe: {await get_burn_safe_status()}"
        send_messages(messages)


    asyncio.run(main())