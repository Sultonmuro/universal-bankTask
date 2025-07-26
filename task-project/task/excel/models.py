from django.db import models
import re
from django.utils import timezone
CARD_STATUS = (
    ('ACTIVE', 'Active'),
    ('EXPIRE', 'Expired'), # Changed for clarity
    ('DECLINED', 'Declined'),
)
# 
class Cards(models.Model):
    card_number = models.CharField(max_length=19,unique=True)
    owner = models.CharField(max_length=20,unique=True)
    expire = models.CharField(max_length=5, help_text= "Expiration date in MM/YY format (e.g., 12/25)")
    phone_number = models.CharField(max_length=15,blank=True,null=True)
    card_status = models.CharField(
        max_length=10,
        choices=CARD_STATUS,
        default='ACTIVE'
    )

    balance = models.DecimalField(max_digits=16,decimal_places=2,default=0.00,help_text="Current balance on the card")




    def __str__(self):
        return f"{self.owner}, {self.card_number}"

    class  Meta:
        ordering = ['owner','card_number']
        verbose_name_plural = "Cards"
class SmsLog(models.Model):
    card = models.ForeignKey(Cards, on_delete=models.CASCADE,related_name='sms_logs')
    message = models.TextField(verbose_name="Сообщение")
    sent_at = models.DateTimeField(auto_now_add=True,verbose_name="Дата отправки")
    success = models.BooleanField(default=True,verbose_name="Успех")

    def __str__(self):
        return f"SMS to {self.card.phone_number} for {self.card.owner} at {self.sent_at.strftime('Y-%m-%d %H:%M')}"


    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Лог SMS/Telegram"
        verbose_name_plural = "Логи SMS/Telegram"
    




    
