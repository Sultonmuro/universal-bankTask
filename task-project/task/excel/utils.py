import re
from datetime import datetime
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

        # --- NEW: Wait for the event loop to be ready ---
        # Polling check to ensure _telegram_loop is not None and is running
        max_attempts = 20 # Try up to 20 times
        attempt = 0
        while not (_telegram_loop and _telegram_loop.is_running()) and attempt < max_attempts:
            logger.debug(f"Waiting for Telegram asyncio loop to start... Attempt {attempt+1}/{max_attempts}")
            time.sleep(0.1) # Wait 100ms before checking again
            attempt += 1
        
        if not (_telegram_loop and _telegram_loop.is_running()):
            raise RuntimeError("Telegram asyncio event loop did not start in time.")
        logger.info("Telegram asyncio loop detected as running.")
        # --- END NEW ---

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
        _botInstance = None # Ensure _botInstance is None if initialization fails
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
        if not self.is_configured: # Rely on the comprehensive check from __init__
            logger.debug(f"TelegramLogger not configured, skipping log message for key '{message_key}'.")
            return False
        
        message_template = settings.TELEGRAM_LOG_MESSAGES.get(message_key, {}).get(lang, 'Error: Message template not found.')

        try:
            formatted_message = message_template.format(**data)
        except KeyError as e:
            logger.error(f"Missing key in data for message_key '{message_key}', lang '{lang}': {e}. Template: '{message_template}'. Data: {data}")
            formatted_message = f"Error formatting message for key '{message_key}': Missing data for {e}. Data: {data}"
            
            # Still attempt to send the error message if the core components are configured
            if settings.TELEGRAM_BOT_CHAT_ID and _telegram_loop and _telegram_loop.is_running():
                try:
                    future = asyncio.run_coroutine_threadsafe(self._send_message_async(settings.TELEGRAM_BOT_CHAT_ID, formatted_message), _telegram_loop)
                    future.result(timeout=5) # Short timeout for error messages
                except Exception as sync_e:
                    logger.error(f"Failed to send Telegram error message via persistent loop: {sync_e}")
            return False # Formatting error means original message wasn't sent
        
        try:
            # The check `if not (_telegram_loop and _telegram_loop.is_running()):` is now redundant here
            # because self.is_configured already covers it.
            
            # Submit the actual message send to the persistent loop
            future = asyncio.run_coroutine_threadsafe(self._send_message_async(settings.TELEGRAM_BOT_CHAT_ID, formatted_message), _telegram_loop)
            telegram_delivery_success = future.result(timeout=30) # Wait up to 30 seconds for delivery

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

    

def card_number(row:str) -> str:
    return  re.sub(r'\D','', row)[:16]
                 # did it myself 
                #HUMO UZCARD diff numbers 
def phone_number(row:str) -> str:
    return re.sub(r'\D','',row)[:20]
            # phone_str = str(row['phone_number']).strip()
            # #
            # cleaned_phone = re.sub(r'\D', '', phone_str) 
            # # regular expressionsda ozini mini languagi bor va '/D' non-digits dgani non digitsla bosa ulani yoqot dgani yani replace with '' blank space
            # row['phone_number'] = cleaned_phone[:20] 
            # #indexation 20 gacha dgani chiqar - > list = [start:end:steps] and we used[:20]
            # #validation 998 12 xonali in case - > operator code(90,99,77 and etc)

def expire_date_sorting(raw_expiry_str: str) ->str:
    match = re.match(r"(\d{1,2})[/\-](/d{2})",raw_expiry_str)
    if match:
         month_part = match.group(1).zfill(2)
         year_part = match.group(2)
         if len(year_part)==4:
              year_part = year_part[2:]
         return f"{month_part}/{year_part}"
    return ""
         
def balance_sorting(row:str)->str:
    balance_lower = str(row).lower().replace('mlrd uzs','').replace(' ','').replace(',','')

     
    try:
                if 'mlrd' in str(row['balance']).lower():
                     value = float(balance_lower) * 1_000_000_000 # Convert to billion
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


def validate_card_expiry(expiry_str:str)->str :
    now = datetime.now()


    try:
        month,year = map(int, str(expiry_str).split("/"))
    except ValueError as e:
        print(f"DEBUG:Invalid format. Returning the error - > {e}")
        return True
     

    if not (1<=month<=12) or not re.match(r"^\d{1,2})/\/d{2}",expiry_str):
        print(f"DEBUG:The format is invalid.")
        return False
    if year<50:
        full_year = 2000+ year
    else:
        full_year = 1900 + year
    

    if month==12:
        expiry_date_month = datetime(full_year,1,1,1) - timedelta(days=1)
    else:
        expiry_date_month = datetime(full_year, month+1,1 ) - timedelta(days=1)

    expiry_last_moment = expiry_date_month.replace(hour=23,minute=59,second=59)

    if expiry_last_moment < now:
        print(f"DEBUG: Card with expiry:{expiry_str} and the moment:{expiry_last_moment}. Card has been expired")
        return True
    else:
        print(f"DEBUG: Card has not been expired. {expiry_str} with the last date - >{expiry_last_moment}")
        return False

