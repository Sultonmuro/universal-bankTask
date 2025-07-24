from django.core.management.base import BaseCommand
from transfers.models import Error

class Command(BaseCommand):
    help = "Populates the Error model with predefined error messages."

    def handle(self, *args, **options):
        errors_to_populate = (
            {"code": 32700, "en": "Ext id must be unique", "ru": "Ext id должен быть уникальным", "uz": "Ext id noyob bo'lishi kerak"},
            {"code": 32701, "en": "Ext id already exists", "ru": "Ext id уже существует", "uz": "Ext id allaqachon mavjud"},
            {"code": 32702, "en": "Balance is not enough", "ru": "Недостаточно средств", "uz": "Hisobda mablag‘ yetarli emas"},
            {"code": 32703, "en": "SMS service is not bind", "ru": "SMS сервис не подключен", "uz": "SMS xizmati ulanmagan"},
            {"code": 32704, "en": "Card expiry is not valid", "ru": "Срок действия карты недействителен", "uz": "Karta amal qilish muddati noto‘g‘ri"},
            {"code": 32705, "en": "Card is not active", "ru": "Карта неактивна", "uz": "Karta faol emas"},
            {"code": 32706, "en": "Unknown error occurred", "ru": "Произошла неизвестная ошибка", "uz": "Noma’lum xatolik yuz berdi"},
            {"code": 32707, "en": "Currency not allowed except 860, 643, 840", "ru": "Разрешены только валюты 860, 643, 840", "uz": "Faqat 860, 643, 840 valyutalari ruxsat etilgan"},
            {"code": 32708, "en": "Amount is greater than allowed", "ru": "Сумма превышает допустимую", "uz": "Miqdor ruxsat etilgan chegaradan katta"},
            {"code": 32709, "en": "Amount is small", "ru": "Сумма слишком мала", "uz": "Miqdor juda kichik"},
            {"code": 32710, "en": "OTP expired", "ru": "OTP истек", "uz": "OTP muddati tugagan"},
            {"code": 32711, "en": "Count of try is reached", "ru": "Превышено количество попыток", "uz": "Urinishlar soni tugadi"},
            {"code": 32712, "en": "OTP is wrong, left try count is 2", "ru": "Неверный OTP, осталось 2 попытки", "uz": "Noto‘g‘ri OTP, yana 2 urinish qoldi"},
            {"code": 32713, "en": "Method is not allowed", "ru": "Метод не разрешён", "uz": "Usulga ruxsat berilmagan"},
            {"code": 32714, "en": "Method not found", "ru": "Метод не найден", "uz": "Usul topilmadi"},
        )
        self.stdout.write(self.style.MIGRATE_HEADING("Populating Error messages"))

        for error_data in errors_to_populate:
            obj, created = Error.objects.get_or_create(
                code = error_data['code'],
                defaults={
                    'en': error_data['en'],
                    'ru': error_data['ru'],
                    'uz': error_data['uz']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Error: {obj.code} - {obj.en}"))
            else:
                self.stdout.write(self.style.ERROR(f"Skipped existing Error: {obj.code} - {obj.en}"))
        self.stdout.write(self.style.SUCCESS("Error messages population complete."))
       