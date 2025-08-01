import re
from datetime import datetime,date
from excel.models import CARD_STATUS,Cards
from datetime import datetime,timedelta
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from django.conf import settings
import logging
from asgiref.sync import async_to_sync
from telegram.ext import Application
import threading
import time
logger = logging.getLogger('__name__')
_botInstance = None
_application = None
_telegram_loop = None
_telegram_loop_thread = None
CARD_PREFIXES = {
    "8600": "HUMO",
    "6262": "UZCARD",
    "4": "VISA",         
    "5": "MASTERCARD",   
 }
def _start_telegram_loop():
    global _telegram_loop
    _telegram_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_telegram_loop)
    logger.info("Telegram asyncio loop started in a new thread.")
    _telegram_loop.run_forever()
    logger.info("Telegram asyncio loop stopped.")

if settings.TELEGRAM_BOT_TOKEN:
    try:
        _telegram_loop_thread = threading.Thread(target=_start_telegram_loop, daemon=True)
        _telegram_loop_thread.start()

       
        max_attempts = 20 
        attempt = 0
        while not (_telegram_loop and _telegram_loop.is_running()) and attempt < max_attempts:
            logger.debug(f"Waiting for Telegram asyncio loop to start... Attempt {attempt+1}/{max_attempts}")
            time.sleep(0.1) 
            attempt += 1
        
        if not (_telegram_loop and _telegram_loop.is_running()):
            raise RuntimeError("Telegram asyncio event loop did not start in time.")
        logger.info("Telegram asyncio loop detected as running.")
    

        async def _init_bot_async():
            global _application, _botInstance
            _application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            _botInstance = _application.bot 
            logger.info("TELEGRAM BOT instance created successfully.")
        
        future = asyncio.run_coroutine_threadsafe(_init_bot_async(), _telegram_loop)
        future.result(timeout=10)

        logger.info("TELEGRAM BOT instance created successfully and ready.")

    except Exception as e:
        logger.error(f"Couldn't create a telegram bot instance: {e}")
        _botInstance = None 
else:
    logger.warning("TELEGRAM_BOT_TOKEN is not configured in settings.")

class TelegramLogger:
    def __init__(self):
        
        self.is_configured = bool(_botInstance and settings.TELEGRAM_BOT_CHAT_ID)
        if not self.is_configured:
            logger.warning("Telegram bot chat id is not configured. Telegram logging will not work")
    
    async def _send_message_async(self,chat_id,text_message):
        if not self.is_configured:
              logger.debug("TelegramLogger is not configured, skipping async message send.")
              return False
        try:
            await _botInstance.send_message(chat_id=chat_id, text=text_message)
            logger.info(f"Successfully sent Telegram log to {chat_id}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram log to {chat_id}. Error: {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending Telegram log: {e}")
            return False 
    def send_log_messages(self, message_key: str, lang: str, data: dict):
        if not self.is_configured: 
            logger.debug(f"TelegramLogger not configured, skipping log message for key '{message_key}'.")
            return False
        
        message_template = settings.TELEGRAM_LOG_MESSAGES.get(message_key, {}).get(lang, 'Error: Message template not found.')

        try:
            formatted_message = message_template.format(**data)
        except KeyError as e:
            logger.error(f"Missing key in data for message_key '{message_key}', lang '{lang}': {e}. Template: '{message_template}'. Data: {data}")
            formatted_message = f"Error formatting message for key '{message_key}': Missing data for {e}. Data: {data}"
            
            
            if settings.TELEGRAM_BOT_CHAT_ID and _telegram_loop and _telegram_loop.is_running():
                try:
                    future = asyncio.run_coroutine_threadsafe(self._send_message_async(settings.TELEGRAM_BOT_CHAT_ID, formatted_message), _telegram_loop)
                    future.result(timeout=5) 
                except Exception as sync_e:
                    logger.error(f"Failed to send Telegram error message via persistent loop: {sync_e}")
            return False # Formatting error means original message wasn't sent
        
        try:
            future = asyncio.run_coroutine_threadsafe(self._send_message_async(settings.TELEGRAM_BOT_CHAT_ID, formatted_message), _telegram_loop)
            telegram_delivery_success = future.result(timeout=30) 

            if telegram_delivery_success:
                logger.debug(f"Successfully sent Telegram message: '{message_key}'")
            else:
                logger.error(f"Telegram message for '{message_key}' failed delivery or encountered an internal async error in persistent loop.")
            
            return telegram_delivery_success
        
        except Exception as e:
            logger.error(f"An error occurred while attempting to send Telegram log message via persistent loop: {e}")
            return False


_telegram_logger_instance = None
def get_telegram_logger():
     global _telegram_logger_instance
     if _telegram_logger_instance is None:
          _telegram_logger_instance = TelegramLogger()
     return _telegram_logger_instance

def validate_UZB_phone_number(row:str) ->str:
    operators = {
         "Uzmobile":99,
         "Beeline":90,
         "Ucel":94,
         "Humans":77
    }
    clean_phone = re.sub(r"\D", "", row)


    if not (len(clean_phone) ==12 and clean_phone.startswith('998')):
        logger.error(f"Validation failed: invalid uzbek phone number format or length")
        raise ValueError(f"Invalid Uzbek phone number: {clean_phone}")
    if not re.match(r"^998\d{2}\d{7}",clean_phone):
        logger.error(f"Validation failed: Final mismatch for cleaned phone numnber: '{clean_phone}'")
        raise ValueError(f"Phone number format mismatch after cleaning: '{row}'")
    

    operator_code_str = clean_phone[3:5]
    try:
        operator_code = int(operator_code_str)
    except ValueError:
        logger.error(f"Validation failed: Could not parse operator code from:{operator_code_str}")

        raise ValueError(f"Invalid operator code in phone number: {row}")
    if operator_code not in operators.values():
        logger.error(f"Validation failed: Operator code '{operator_code}' not recognized")
        raise ValueError(f"Operator code: '{operator_code}' not recognized for phone numbers in Uzbekistan.")
    
    logger.info(f"phone number '{clean_phone}' is valid and belongs to a recognized operator")
    return clean_phone


 


    


def validate_UZB_card_numbers(row:str) -> str:
    cleaned_card_number = card_number(row=row)

    detected_card_type = "UNKNOWN"

    sorted_prefixes = sorted(CARD_PREFIXES.keys(),key=len,reverse=True)


    for prefix in sorted_prefixes:
        if cleaned_card_number.startswith(prefix):
            detected_card_type = CARD_PREFIXES[prefix]
            break
    
    if detected_card_type == "UNKNOWN":
        logger.error(f"ERROR: We could not detect any card number. {cleaned_card_number}")
    

    match detected_card_type:
         case "HUMO":
            logger.info(f"DEBUG: This is a Humo card. from prefix {prefix}")
         case 'UZCARD':
            logger.info(f"DEBUG: THIS IS UZCARD (from prefix: {prefix})")
            
         case 'VISA':
            logger.info(f"DEBUG: THIS IS VISA CARD (from prefix: {prefix})")
            
         case 'MASTERCARD':
            logger.info(f"DEBUG: THIS IS MASTERCARD (from prefix: {prefix})")
            
         case _:
            logger.info(f"ERROR: Unexpected card type: {detected_card_type}. This should have been caught.")
            return False
    if len(cleaned_card_number) ==16:
        return cleaned_card_number
    else:
        logger.error("Invalid length of card number.")    
    
def card_number(row:str) -> str:
    return  re.sub(r'\D','', row)[:16]
def phone_number(row:str) -> str:
    return re.sub(r"\D", "", row)

def balance_sorting(row:str)->str:
    balance_lower = str(row).lower().replace('mlrd uzs','').replace(' ','').replace(',','')

     
    try:
                if 'mlrd' in str(row['balance']).lower():
                     value = float(balance_lower) * 1_000_000_000 
                else:
                    value = float(balance_lower)
                row['balance'] = str(round(value, 2))
    except ValueError:
                row['balance'] = '0.00'
def card_status(row:str)->str:
            if 'card_status' in row and row['card_status']:
                status_upper = str(row['card_status']).upper()
                valid_statuses = [choice[0] for choice in CARD_STATUS]
                if status_upper not in valid_statuses:
                    row['card_status'] = 'ACTIVE' 
                # else:
                #     row['card_status'] = 'EXPIRED'
                #MAKE IT expire in case if expire date is literally expired  

def expire_date_sorting(raw_expiry_str: str) -> date:
    expiry_str = raw_expiry_str.strip()

    match = re.match(r"^(\d{1,2})/(\d{2})$", expiry_str)
    if not match:
        raise ValueError(f"Invalid expiry date format. Expected MM/YY (e.g., 12/25). Got: '{expiry_str}'")

    month_str, year_str = match.groups()

    try:
        month = int(month_str)
        year_short = int(year_str)
    except ValueError: 
        raise ValueError(f"Invalid month or year value in expiry date: '{expiry_str}'")

    if not (1 <= month <= 12):
        raise ValueError(f"Month must be between 01 and 12. Got: '{month_str}'.")

    current_year_full = date.today().year 
    current_year_two_digit = current_year_full % 100

    if year_short >= (current_year_two_digit - 20) and year_short <= (current_year_two_digit + 20):
        full_year = (current_year_full // 100) * 100 + year_short
    elif year_short > (current_year_two_digit + 20): 
        full_year = (current_year_full // 100 - 1) * 100 + year_short
    else: 
        full_year = (current_year_full // 100 + 1) * 100 + year_short
    
    try:
        if month == 12:
            last_day_of_month = date(full_year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day_of_month = date(full_year, month + 1, 1) - timedelta(days=1)
            
        return last_day_of_month 
    except ValueError:
        raise ValueError(f"Invalid date values: {month}/{year_short}. Cannot form a valid date.")
    


def validate_card_expiry(expiry_str:date,data_container:dict) -> None:
    now = date.today() 
    print(f"DEBUG validate_card_expiry: parsed_expiry_date: {expiry_str} (type: {type(expiry_str)})")
    print(f"DEBUG validate_card_expiry: now_date: {now} (type: {type(now)})")
    if expiry_str < now:
        print(f"DEBUG: Card with expiry:{expiry_str} and the moment:{expiry_str}. Card has been expired")
        data_container['card_status'] = "EXPIRE"
    else:
        print(f"DEBUG: Card has not been expired. {expiry_str}")
        data_container["card_status"] = "ACTIVE"

