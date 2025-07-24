import re
from datetime import datetime
from excel.models import CARD_STATUS,Cards
from datetime import datetime,timedelta



def card_number(row):
    return  re.sub(r'\D','', row['card_number'])[:16]
                 # did it myself 
                #HUMO UZCARD diff numbers 
def phone_number(row):
    return re.sub(r'\D','',row)[:20]
            # phone_str = str(row['phone_number']).strip()
            # #
            # cleaned_phone = re.sub(r'\D', '', phone_str) 
            # # regular expressionsda ozini mini languagi bor va '/D' non-digits dgani non digitsla bosa ulani yoqot dgani yani replace with '' blank space
            # row['phone_number'] = cleaned_phone[:20] 
            # #indexation 20 gacha dgani chiqar - > list = [start:end:steps] and we used[:20]
            # #validation 998 12 xonali in case - > operator code(90,99,77 and etc)

def expire_date_sorting(raw_expiry_str: str) ->bool:
    match = re.match(r"(\d{1,2})[/\-](/d{2})",raw_expiry_str)
    if match:
         month_part = match.group(1).zfill(2)
         year_part = match.group(2)
         if len(year_part)==4:
              year_part = year_part[2:]
         return f"{month_part}/{year_part}"
    return ""
         
def balance_sorting(row):
    balance_lower = str(row).lower().replace('mlrd uzs','').replace(' ','').replace(',','')

     
    try:
                if 'mlrd' in str(row['balance']).lower():
                     value = float(balance_lower) * 1_000_000_000 # Convert to billion
                else:
                    value = float(balance_lower)
                row['balance'] = str(round(value, 2))
    except ValueError:
                row['balance'] = '0.00'
def card_status(row):
            if 'card_status' in row and row['card_status']:
                status_upper = str(row['card_status']).upper()
                valid_statuses = [choice[0] for choice in CARD_STATUS]
                if status_upper not in valid_statuses:
                    row['card_status'] = 'ACTIVE' 
                # else:
                #     row['card_status'] = 'EXPIRED'
                #MAKE IT expire in case if expire date is literally expired  


def validate_card_expiry(expiry_str:str) -> bool:
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

def 