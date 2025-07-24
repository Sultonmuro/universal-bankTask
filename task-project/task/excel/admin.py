from django.contrib import admin
from .models import Cards,CARD_STATUS,SmsLog
from import_export import resources,fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import DateTimeWidget
from django.contrib import messages
from datetime import datetime
import re
from .utils import *
class CardResource(resources.ModelResource):
    expire = fields.Field(attribute='expire',column_name='expire')


    class Meta:
        model = Cards
        fields = ('card_number','owner','expire','phone_number','card_status','balance')
    
    def before_import_row(self, row, **kwargs):
        
        card_number(row)
        expire_date_sorting(row)
        phone_number(row=row)
        balance_sorting(row)
        card_status(row)

        

    
        return super().before_import_row(row, **kwargs)
    def get_instance(self, instance_loader, row):
        try:
            return self.Meta.model.objects.get(card_number=row.get('card_number'))
        except self.Meta.model.DoesNotExist:
            return None
@admin.action(description='Send SMS to selected cards')
def send_sms_action(modeladmin, request, queryset):
    sent_count = 0
    log_messages = []

    for card in queryset:
        if card.phone_number:
            message_content = f"Xurmatli {card.owner}, sizning karta raqamingizda {card.card_number[-4:]} balans {card.balance} UZS. Status: {card.get_card_status_display()}."
            
         
            SmsLog.objects.create(
                card=card,
                message=message_content,
                success=True 
            )
            log_messages.append(f"SMS sent to {card.owner} ({card.phone_number}) for card {card.card_number}.")
            sent_count += 1
        else:
            log_messages.append(f"Skipped SMS for {card.owner} (Card: {card.card_number}) - No phone number.")

    if sent_count > 0:
        modeladmin.message_user(request, f"Successfully simulated sending SMS to {sent_count} card(s).", messages.SUCCESS)
    else:
        modeladmin.message_user(request, "No SMS were sent (either no cards selected or no phone numbers found).", messages.WARNING)

    
    for msg in log_messages:
        modeladmin.message_user(request, msg, messages.INFO)


@admin.register(Cards)
class CardsAdmin(ImportExportModelAdmin):
    resource_class = CardResource
    list_display = ('card_number', 'owner', 'expire', 'phone_number', 'card_status', 'balance',)
    list_filter = ('card_status', 'owner',) 
    search_fields = ('card_number', 'owner', 'phone_number',) 
    actions = [send_sms_action] 
@admin.register(SmsLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('card', 'message', 'sent_at', 'success',)
    list_filter = ('sent_at', 'success', 'card__card_status',) 
    search_fields = ('card__card_number', 'card__owner', 'message',)
    readonly_fields = ('card', 'message', 'sent_at', 'success',)
    
