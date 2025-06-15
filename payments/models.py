# payments/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from orders.models import Order
from accounts.models import User


class Payment(models.Model):
    """
    To'lovlar modeli - Avans, qisman va yakuniy to'lovlar
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Naqd pul'),
        ('card', 'Plastik karta'),
        ('bank_transfer', 'Bank o\'tkazmasi'),
        ('click', 'Click'),
        ('payme', 'Payme'),
        ('uzcard', 'UzCard'),
        ('humo', 'Humo'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('advance', 'Avans to\'lov'),
        ('partial', 'Qisman to\'lov'),
        ('final', 'Yakuniy to\'lov'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Buyurtma'
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='partial',
        verbose_name='To\'lov turi'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='To\'lov miqdori'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        verbose_name='To\'lov usuli'
    )
    payment_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='To\'lov sanasi'
    )
    
    # Qo'shimcha ma'lumotlar
    receipt_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Kvitansiya raqami'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_payments',
        verbose_name='Qabul qiluvchi'
    )
    
    # Tasdiqlash maydonlari
    is_confirmed = models.BooleanField(
        default=True,
        verbose_name='Tasdiqlangan'
    )
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_payments',
        verbose_name='Tasdiqlovchi'
    )
    confirmed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Tasdiqlangan vaqt'
    )
    
    # Sanalar
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan vaqt'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='O\'zgartirilgan vaqt'
    )
    
    class Meta:
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"#{self.order.order_number} - {self.amount:,.0f} so'm ({self.get_payment_type_display()})"
    
    def save(self, *args, **kwargs):
        """Saqlashda avtomatik tasdiqlash vaqtini belgilash"""
        if self.is_confirmed and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_payment_status_display(self):
        """To'lov holati ko'rsatish"""
        if self.is_confirmed:
            return "Tasdiqlangan"
        else:
            return "Tasdiqlanmagan"
    
    def get_payment_status_class(self):
        """Bootstrap class"""
        if self.is_confirmed:
            return "success"
        else:
            return "warning"