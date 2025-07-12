# customers/models.py - TO'G'IRLANGAN VERSIYA

from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.conf import settings
import uuid


class Customer(models.Model):
    """
    Mijozlar modeli - Telegram integration bilan yangilangan
    """
    
    # YANGI: Mijoz kategoriyalari
    CATEGORY_CHOICES = [
        ('new', 'Yangi'),
        ('regular', 'Oddiy'),
        ('vip', 'VIP'),
        ('inactive', 'Nofaol'),
    ]
    
    # Asosiy ma'lumotlar
    first_name = models.CharField(
        max_length=50,
        verbose_name='Ism'
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name='Familiya'
    )
    
    # YANGI: Tug'ilgan kun
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Tug\'ilgan kun',
        help_text='Tug\'ilgan kunni kiritish tabriklash uchun foydali'
    )
    
    # YANGI: Mijoz kategoriyasi
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='new',
        verbose_name='Kategoriya',
        help_text='Mijoz kategoriyasi (yangi, oddiy, VIP)'
    )
    
    # Asosiy telefon raqam (mavjud)
    phone = models.CharField(
        max_length=15,
        verbose_name='Asosiy telefon raqam',
        help_text='Asosiy aloqa telefon raqami'
    )
    
    # YANGI: Telegram ID field
    telegram_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        verbose_name='Telegram ID',
        help_text='Telegram bot orqali registratsiya qilingan foydalanuvchi ID'
    )
    
    # Manzil va izoh
    address = models.TextField(
        verbose_name='Manzil'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    
    # YANGI: Kim qo'shgan
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_customers',
        verbose_name='Qo\'shgan xodim'
    )
    
    # Mijoz uchun maxsus identifikator
    public_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='Umumiy identifikator'
    )
    
    # Vaqt belgilari
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Qo\'shilgan sana'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='O\'zgartirilgan sana'
    )
    
    class Meta:
        verbose_name = 'Mijoz'
        verbose_name_plural = 'Mijozlar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['phone']),
            models.Index(fields=['category']),
            models.Index(fields=['telegram_id']),  # YANGI index
        ]
    
    def __str__(self):
        return self.get_full_name()
    
    def get_full_name(self):
        """To'liq ism qaytaradi"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_absolute_url(self):
        """Mijoz sahifasiga havola"""
        return reverse('customers:detail', kwargs={'pk': self.pk})
    
    def get_public_url(self):
        """Mijoz uchun public sahifa havolasi"""
        return reverse('customers:public_detail', kwargs={'uuid': self.public_uuid})
    
    def get_telegram_public_url(self):
        """YANGI: Telegram ID bilan public sahifa havolasi"""
        if self.telegram_id:
            return reverse('customers:telegram_public', kwargs={'tgid': self.telegram_id})
        return None
    
    def total_orders(self):
        """Umumiy buyurtmalar soni"""
        return self.orders.count()
    total_orders.short_description = 'Buyurtmalar soni'
    
    def total_paid_amount(self):
        """To'langan umumiy summa"""
        from payments.models import Payment
        return Payment.objects.filter(
            order__customer=self,
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    def total_debt(self):
        """Qarzdorlik summasi"""
        total_order_amount = sum(order.total_price() for order in self.orders.all())
        total_paid = self.total_paid_amount()
        return max(0, total_order_amount - total_paid)
    
    def get_age(self):
        """YANGI: Yoshni hisoblash"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None
    
    def is_complete_profile(self):
        """YANGI: Profil to'liqligini tekshirish"""
        required_fields = [self.first_name, self.last_name, self.phone, self.address]
        return all(field and field.strip() for field in required_fields)
    
    @classmethod
    def get_by_telegram_id(cls, telegram_id):
        """YANGI: Telegram ID bo'yicha mijozni topish"""
        try:
            return cls.objects.get(telegram_id=str(telegram_id))
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def create_from_telegram(cls, telegram_id, phone_number, first_name=None, last_name=None):
        """YANGI: Telegram ma'lumotlaridan mijoz yaratish"""
        customer = cls.objects.create(
            telegram_id=str(telegram_id),
            phone=phone_number,
            first_name=first_name or '',
            last_name=last_name or '',
            address='',  # Bo'sh manzil, keyinchalik to'ldiriladi
            category='new'
        )
        return customer

class CustomerPhone(models.Model):
    """
    Mijozning qo'shimcha telefon raqamlari
    """
    
    PHONE_TYPE_CHOICES = [
        ('mobile', 'Mobil'),
        ('home', 'Uy'),
        ('work', 'Ish'),
        ('other', 'Boshqa'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='additional_phones',
        verbose_name='Mijoz'
    )
    
    phone_number = models.CharField(
        max_length=15,
        verbose_name='Telefon raqam',
        validators=[
            RegexValidator(
                regex=r'^\+?998\d{9}$',
                message='To\'g\'ri formatda telefon raqam kiriting: +998901234567'
            )
        ]
    )
    
    phone_type = models.CharField(
        max_length=20,
        choices=PHONE_TYPE_CHOICES,
        default='mobile',
        verbose_name='Telefon turi'
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Asosiy telefon'
    )
    
    notes = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Qo\'shilgan sana'
    )
    
    class Meta:
        verbose_name = 'Telefon raqam'
        verbose_name_plural = 'Telefon raqamlar'
        unique_together = ['customer', 'phone_number']
        ordering = ['-is_primary', '-created_at']
    
    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.phone_number}"


class CustomerNote(models.Model):
    """
    YANGI: Mijoz haqida eslatmalar (xodimlar tomonidan)
    """
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='customer_notes',
        verbose_name='Mijoz'
    )
    
    note = models.TextField(
        verbose_name='Eslatma'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Yozgan xodim'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana'
    )
    
    is_important = models.BooleanField(
        default=False,
        verbose_name='Muhim eslatma'
    )
    
    class Meta:
        verbose_name = 'Mijoz eslatmasi'
        verbose_name_plural = 'Mijoz eslatmalari'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.note[:50]}..."