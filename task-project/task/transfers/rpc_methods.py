from jsonrpcserver import method, InvalidParams
from .models import Transfer,Error
from excel.models import Cards
import logging
from excel import models
from excel.utils import *
from .utils import * 

logger = logging.getLogger("__name__")

@models
def transfer_create(ext_id:int,sender_card:str,receiver_card:str,currency):
    
    clean_card = validate_card_expiry(sender_card)
    new_transfer = Transfer()

    