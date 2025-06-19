# customers/models.py - TO'G'IRLANGAN VERSIYA

from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.conf import settings
import uuid


class Customer(models.Model):
    """
    Mijozlar modeli - Yangilangan versiya
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
    
    def total_orders(self):
        """Umumiy buyurtmalar soni"""
        return self.orders.count()
    total_orders.short_description = 'Buyurtmalar soni'
    
    def total_paid_amount(self):
        """To'langan umumiy summa"""
        from payments.models import Payment
        return Payment.objects.filter(
            order__customer=self,
            is_confirmed=True
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
    
    def get_category_display_badge(self):
        """YANGI: Kategoriya badge rangi"""
        badge_classes = {
            'new': 'badge bg-info',
            'regular': 'badge bg-secondary',
            'vip': 'badge bg-warning text-dark',
            'inactive': 'badge bg-danger',
        }
        return badge_classes.get(self.category, 'badge bg-secondary')
    
    def is_birthday_today(self):
        """YANGI: Bugun tug'ilgan kun ekanligini tekshirish"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return (today.month == self.birth_date.month and 
                   today.day == self.birth_date.day)
        return False
    
    def days_until_birthday(self):
        """YANGI: Tug'ilgan kungacha qolgan kunlar"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            birthday_this_year = self.birth_date.replace(year=today.year)
            
            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)
            
            return (birthday_this_year - today).days
        return None


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