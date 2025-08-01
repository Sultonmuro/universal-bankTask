# Generated by Django 5.2.4 on 2025-07-25 13:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cards',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_number', models.CharField(max_length=19, unique=True)),
                ('owner', models.CharField(max_length=20)),
                ('expire', models.CharField(help_text='Expiration date in MM/YY format (e.g., 12/25)', max_length=5)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('card_status', models.CharField(choices=[('ACTIVE', 'Active'), ('EXPIRE', 'Expired'), ('DECLINED', 'Declined')], default='ACTIVE', max_length=10)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, help_text='Current balance on the card', max_digits=16)),
            ],
            options={
                'verbose_name_plural': 'Cards',
                'ordering': ['owner', 'card_number'],
            },
        ),
        migrations.CreateModel(
            name='SmsLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(verbose_name='Сообщение')),
                ('sent_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')),
                ('success', models.BooleanField(default=True, verbose_name='Успех')),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sms_logs', to='excel.cards')),
            ],
            options={
                'verbose_name': 'Лог SMS/Telegram',
                'verbose_name_plural': 'Логи SMS/Telegram',
                'ordering': ['-sent_at'],
            },
        ),
    ]
