# Generated by Django 5.2.3 on 2025-06-21 10:12

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=50, verbose_name='Ism')),
                ('last_name', models.CharField(max_length=50, verbose_name='Familiya')),
                ('birth_date', models.DateField(blank=True, help_text="Tug'ilgan kunni kiritish tabriklash uchun foydali", null=True, verbose_name="Tug'ilgan kun")),
                ('category', models.CharField(choices=[('new', 'Yangi'), ('regular', 'Oddiy'), ('vip', 'VIP'), ('inactive', 'Nofaol')], default='new', help_text='Mijoz kategoriyasi (yangi, oddiy, VIP)', max_length=20, verbose_name='Kategoriya')),
                ('phone', models.CharField(help_text='Asosiy aloqa telefon raqami', max_length=15, verbose_name='Asosiy telefon raqam')),
                ('address', models.TextField(verbose_name='Manzil')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Izoh')),
                ('public_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Umumiy identifikator')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan sana")),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_customers', to=settings.AUTH_USER_MODEL, verbose_name="Qo'shgan xodim")),
            ],
            options={
                'verbose_name': 'Mijoz',
                'verbose_name_plural': 'Mijozlar',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CustomerNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(verbose_name='Eslatma')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')),
                ('is_important', models.BooleanField(default=False, verbose_name='Muhim eslatma')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Yozgan xodim')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_notes', to='customers.customer', verbose_name='Mijoz')),
            ],
            options={
                'verbose_name': 'Mijoz eslatmasi',
                'verbose_name_plural': 'Mijoz eslatmalari',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CustomerPhone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15, validators=[django.core.validators.RegexValidator(message="To'g'ri formatda telefon raqam kiriting: +998901234567", regex='^\\+?998\\d{9}$')], verbose_name='Telefon raqam')),
                ('phone_type', models.CharField(choices=[('mobile', 'Mobil'), ('home', 'Uy'), ('work', 'Ish'), ('other', 'Boshqa')], default='mobile', max_length=20, verbose_name='Telefon turi')),
                ('is_primary', models.BooleanField(default=False, verbose_name='Asosiy telefon')),
                ('notes', models.CharField(blank=True, max_length=100, null=True, verbose_name='Izoh')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_phones', to='customers.customer', verbose_name='Mijoz')),
            ],
            options={
                'verbose_name': 'Telefon raqam',
                'verbose_name_plural': 'Telefon raqamlar',
                'ordering': ['-is_primary', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['first_name', 'last_name'], name='customers_c_first_n_146a71_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['phone'], name='customers_c_phone_8493fa_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['category'], name='customers_c_categor_f85c24_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='customerphone',
            unique_together={('customer', 'phone_number')},
        ),
    ]
