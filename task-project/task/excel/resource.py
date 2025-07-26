from import_export import fields
from import_export import resources
from .models import Cards,CARD_STATUS
from.utils import(
    card_number,
    phone_number,
    expire_date_sorting,
    balance_sorting,
    card_status,
    validate_card_expiry
)
import logging 

logger = logging.getLogger('__name__')


class CardResource(resources.ModelResource):
    class Meta:
        model = Cards
    


    def before_import_row(self, row, **kwargs):

        if 'card_number' in row and row['card_number']:
            row['card_number'] = card_number(str(row['card_number']))

        if 'phone_number' in row and row['phone_number']:
            row['phone_number'] = phone_number(str(row['phone_number']))
        
        if 'expire' in row and row['expire']:
            cleaned_expire = expire_date_sorting(str(row['expire']))

            if cleaned_expire:
                row['expire'] = cleaned_expire
                if validate_card_expiry(cleaned_expire):

                    row['card_status'] = 'EXPIRED'
                else:
                    if 'card_status' in row and row['card_status']:
                        row['card_status'] = card_status(str(row['card_status']))
                    else:
                        row['card_status'] = 'ACTIVE'
            else:
                row['card_status'] = 'EXPIRED'
        #balance sorting   
        if 'balance' in row and row['balance']:
            row['balance'] = balance_sorting(str(row['balance']))
        
       
        


        return super().before_import_row(row, **kwargs)
