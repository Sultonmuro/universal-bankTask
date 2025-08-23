from jsonrpcserver import method,serve
from jsonrpcserver import method, InvalidParams
from .models import Transfer,Error
from excel.models import Cards
import logging
from excel import models
from excel.utils import *
from .utils import * 
from django.views.decorators.csrf import csrf_exempt
from jsonrpcserver import dispatch
import json
from excel.utils import *
from transfers.utils import *

@method 
def transfer_create(ext_id,sender_card_number:str,sender_card_expiry:str,receiver_card_number:str,
                    sender_phone:str,sending_amount:str,currency:str):
    sender_card = validate_UZB_card_numbers(sender_card_number)
    if not sender_card:
        return {"error":"Invalid sender card"}
    
    
    otp= generate_otp()
    send_telegram_message(sender_phone,f"Your OTP is {otp}")

    transfer = Transfer.objects.create(
        ext_id=ext_id,
        sender_card_number=sender_card_number,
        sender_card_expiry=sender_card_expiry,
        receiver_card_number=receiver_card_number,
        sending_amount=sending_amount,
        currency=currency,
        otp=otp,
        state="created",
    )
    transfer.save()
    return {"ext_id":transfer.ext_id,"state":transfer.state,"otp_sent":transfer.otp}


@method 
def transfer_confirm(ext_id,otp):
    validation = validate_otp(ext_id=ext_id,otp=otp)
    return validation

@method 
def transfer_history(card_number:str,start_date:str,end_date:str,status:str):
    read_transfers =view_transfers(card_number,start_date,end_date,status)
    transfers = list()

    # for transfer in read_transfers:
    #     transfers.append(
    #         {
    #             "ext_id":str(transfer.ext_id),
    #             "sending_amount":transfer.sending_amount,
    #             "state":transfer.state,
    #             "created_at":transfer.created_at
    #         }
    #     )
    #     transfer.save()
    
    return {"transfers":transfers}

@method 
def transfer_cancel(ext_id):
    transfer = Transfer.objects.get(ext_id=ext_id)
    if not transfer:
        logging.error(f"'{ext_id}'- Not found")
    transfer.state = "cancelled"
    transfer.save()
    return {"state":transfer.state}

@method 
def view_transfer_list(ext_id):
    transfer = Transfer.objects.get(ext_id=ext_id)
    end_date = ""

    try:
        if transfer:
            if transfer.state == "cancelled":
                end_date = transfer.cancelled_at
            else:
                end_date = None
            return {
                "card_number":transfer.sender_card_number,
                "start_date":str(transfer.created_at),
                "end_date":str(end_date),
                "status":transfer.state
            }
    except Transfer.DoesNotExist as e:
        logging.error("Not Found")
        return {"error":"Not Found"}
    