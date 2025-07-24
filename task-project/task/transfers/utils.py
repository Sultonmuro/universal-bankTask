import random 
import string 
import re
from datetime import datetime
from django.conf import settings 
from excel.models import Cards
from transfers.models import Error,Transfer,TRANSFER_STATE_CHOICES,CURRENCY_TYPE

def generate_otp(length=6):
    return "".join(random.choice(string.digits, length))
def send_telegram_message(phone,message,chat_Id=None):
    if chat_Id is None:
        chat_Id = settings.TELEGRAM_CHAT_ID
    

   