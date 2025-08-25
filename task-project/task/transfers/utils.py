import random 
import string 
import re
import requests
from datetime import datetime
from django.conf import settings 
from django.db.models import Q
from excel.models import Cards
from transfers.models import Error,Transfer,TRANSFER_STATE_CHOICES,CURRENCY_TYPE
import logging
from jsonrpcserver import InvalidParams


logger = logging.getLogger("__name__")

def generate_otp(length=6):
    otp =""

    for _ in range(length):
        otp +=random.choice(string.digits)
    return otp
def send_telegram_message(phone,message,chat_id:str=None):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_BOT_CHAT_ID
    if not chat_id:
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
def validate_otp(ext_id,otp):
    
    transfer= Transfer.objects.get(ext_id=ext_id)
    if not transfer:
        logging.error("Not found")
        raise InvalidParams("Transfer Not found.")
    
    otp_vd = Transfer.objects.get(otp=otp) # vd = validated
    if not otp_vd:
        logging.error("Wrong OTP")
        transfer.try_count+=1
        raise Exception("Wrong OTP")
    if transfer.try_count >=3:
        transfer.state ="blocked"
        raise Exception("Used all 3 attempts.Transfer status=",transfer.state)
    transfer.state="confirmed"
    transfer.confirmed_at = datetime.now()
    transfer.save()
    logging.info(f"{otp} is matching the real otp for '{ext_id}' id. Confirmed")
    return {"success":True,
            "status":transfer.state,
            "time":str(transfer.confirmed_at)}

        

def view_transfers(card_number:str,start_date:str,end_date:str,status:str):
    try:
            filtered_transfer = Q(receiver_card_number=card_number)& Q(state=status)
        
            if start_date and end_date !="None":
               filtered_transfer &=Q(created_at__range=[start_date,end_date])
            elif start_date:
               filtered_transfer &=Q(created_at__gte=start_date)
            filtered_transfers = Transfer.objects.filter(filtered_transfer)
            if not filtered_transfer:
                return []
            return [{
               "ext_id":t.ext_id,
               "sending_amount":t.sending_amount,
               "state":t.state,
               "created_at":t.created_at
           }  for t in filtered_transfers]
    except Transfer.DoesNotExist as e:
        logging.error("Not Found", e)
        return {"error":"Not Found"}
    
    






def get_transfer_by_ext_id(ext_id):
    byId = Transfer.objects.get(ext_id=ext_id)
    try:
        if byId:
         return {"sender_card":byId.sender_card_number,
                "receiver_card":byId.receiver_card_number,
                "amount":byId.sending_amount,
                "currency":byId.currency}
    except Transfer.DoesNotExist as e:
        logging.error(f"Transfer with '{byId}' ext_id is not found")
        return {"error":"Not found"}


def read_tf():
    read = Transfer.objects.all()
    if not read:
        return []
    return [{
        "ext_id":t.ext_id,
        "card_number":t.receiver_card_number,
        "status":t.state,
        "created_at":str(t.created_at),
        "confirmed_at":str(t.confirmed_at),
        "otp":t.otp
    }for t in read
    ]



    

