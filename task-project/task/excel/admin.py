

from django.contrib import admin
from .models import Cards,CARD_STATUS,SmsLog
from import_export import resources,fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import DateTimeWidget
from django.contrib import messages
from datetime import datetime
import re
from .utils import *
from .forms import CardAdminForms
from .resource import CardResource
import time
telegram_logger = get_telegram_logger()
 
def before_import_row(self, row, **kwargs):
    
    if 'card_number' in row and row['card_number']:
        row['card_number']= validate_UZB_card_numbers(str(row['card_number']))
    

    if 'balance' in row and row['balance']:
        row['balance'] = balance_sorting(str(row['balance']))
    if 'card_status' in row and row['card_status']:
        row['card_status'] = card_status(str(row['card_status']))

    if 'expire' in row and row['expire']:
        sorted_expiry = expire_date_sorting(str(row['expire']))
        if sorted_expiry:
            is_expired = validate_card_expiry(sorted_expiry,row) 
            if is_expired:
                row['card_status'] = "EXPIRED"
            else: # Card is not expired
                row['card_status'] = "ACTIVE"

    if 'phone_number' in row and row['phone_number']:
        row['phone_number']= validate_UZB_card_numbers(str(row['phone_number']))
    

        # card_number(row)
        # expire_date_sorting(row)

        
        # balance_sorting(row)
        # card_status(row)

@admin.action(description='Send SMS to selected cards')
def send_sms_action(modeladmin, request, queryset):
    sent_count = 0

    admin_lang = 'ru'

    for card in queryset:
        if card.phone_number:
            message_data = {
                'owner': card.owner,
                'last_4_digits': card.card_number[-4:], 
                'balance': card.balance,
                'status': card.get_card_status_display()
            }

            owner_telegram_lang = 'uz'


            telegram_success = telegram_logger.send_log_messages('card_balance_status', owner_telegram_lang, message_data)

            SmsLog.objects.create(
                card=card,
                message=settings.TELEGRAM_LOG_MESSAGES['card_balance_status'].get(owner_telegram_lang, '').format(**message_data),
                success=telegram_success
            )
            
            if telegram_success:
                
                modeladmin.message_user(request, f"Telegram notification initiated for {card.owner} (PHONE: {card.phone_number}) for card {card.card_number}. ", messages.INFO)
                sent_count +=1
            else:
                modeladmin.message_user(request, f"Failed to send Telegram notification for {card.owner} (Phone: {card.phone_number}) for card {card.card_number}.", messages.ERROR)
            time.sleep(0.01)
        else:
            skipped_data = {
                'owner': card.owner,
                'card_number': card.card_number,
            }
            
            telegram_logger.send_log_messages('no_phone_number', admin_lang, skipped_data)

            modeladmin.message_user(request,f"Skipped Telegram notification for {card.owner} (Card: {card.card_number}) - No phone number.", messages.WARNING)
            SmsLog.objects.create(
                card=card,
               
                message=settings.TELEGRAM_LOG_MESSAGES['no_phone_number'].get(admin_lang,'').format(**skipped_data),
                success=False
            )

    if sent_count > 0:
        success_message_template = settings.TELEGRAM_LOG_MESSAGES['simulated_sms_sent'].get(admin_lang,'').format(count=sent_count)
        modeladmin.message_user(request, success_message_template, messages.SUCCESS)
    else:
        # <--- ИСПРАВЛЕНО: 'no_sms_sent' (с нижним подчеркиванием)
        warning_message_template = settings.TELEGRAM_LOG_MESSAGES['no_sms_sent'].get(admin_lang,'')
        modeladmin.message_user(request, warning_message_template, messages.WARNING)


# <--- ИСПРАВЛЕНО: @admin.register(Card) (не Cards)
@admin.register(Cards)
class CardAdmin(ImportExportModelAdmin):

    form =CardAdminForms
    resource_class = CardResource
    list_display = ('card_number', 'owner', 'expire', 'phone_number', 'card_status', 'balance',) 
    list_filter = ('card_status', 'owner',) 
    search_fields = ('card_number', 'owner', 'phone_number',)
    actions = [send_sms_action]


    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change) 
        print(f"DEBUG ADMIN: save_model - obj.card_status AFTER super(): {obj.card_status}")
@admin.register(SmsLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('card', 'message', 'sent_at', 'success',)
    list_filter = ('sent_at', 'success', 'card__card_status',)
    search_fields = ('card__card_number', 'card__owner', 'message',)
    readonly_fields = ('card', 'message', 'sent_at', 'success',)

