import random 
import string 
import re
import requests
from datetime import datetime
from django.conf import settings 
from excel.models import Cards
from transfers.models import Error,Transfer,TRANSFER_STATE_CHOICES,CURRENCY_TYPE
import logging

logger = logging.getLogger("__name__")

def generate_otp(length=6):
    return "".join(random.choice(string.digits, length))
def send_telegram_message(phone,message,chat_id:str):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_BOT_CHAT_ID
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(telegram_url, json={'chat_id': chat_id, 'text': message})
        response.raise_for_status()
        logger.info(f"Telegram message sent successfully to {phone}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send a telegram message. Due to {e}")
        return False

