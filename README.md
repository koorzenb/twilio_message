# Twilio Message

Website monitoring system that detects changes and sends SMS notifications via Twilio.

## Quick Start

1. **Get Twilio credentials** - Sign up at [twilio.com](https://twilio.com)
2. **Set up environment** - Copy `.env.example` to `.env` and add your credentials
3. **Install dependencies** - Run `pip install -r src/requirements.txt`
4. **Run a scraper** - See commands below

## Available Scrapers

- **BurnSafe Scraper** - Nova Scotia burn restrictions
- **Sponsor Parents Scraper** - Canada.ca immigration updates  
- **Example Scraper** - Template for any website

## Creating Your Own Scraper

see main.py -> send_email_update() for process flow

## Environment Variables (.env)

```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
MY_PHONE_NUMBER=your_recipient_phone_number
```

---

📋 **For detailed technical documentation, architecture details, and development guidelines, see [PRD.md](PRD.md)**
