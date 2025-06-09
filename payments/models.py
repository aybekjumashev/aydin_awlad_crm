# payments/models.py

from django.db import models
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
        related_name='received_payments',  # Bu qatorni qo'shamiz
        verbose_name='Qabul qiluvchi'
    )
    
    # Maydonga bog'liq maydonlar
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
    
    class Meta:
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_payment_type_display()} - {self.amount:,} so'm"
    
    def save(self, *args, **kwargs):
        # Agar tasdiqlanmagan bo'lsa, avtomatik tasdiqlash
        if not self.confirmed_at and self.is_confirmed:
            from django.utils import timezone
            self.confirmed_at = timezone.now()
        
        # Yangi to'lov yaratilganda history ga yozish
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.order:
            # Order history ga to'lov qabul qilingani haqida yozuv
            self.order.create_history(
                action='payment_received',
                performed_by=self.received_by,
                notes=f"{self.get_payment_type_display()}: {self.amount:,} so'm ({self.get_payment_method_display()})"
            )