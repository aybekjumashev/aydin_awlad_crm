# payments/models.py - TO'G'IRLANGAN VERSIYA

from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal


class Payment(models.Model):
    """
    To'lovlar modeli - Yangilangan versiya
    """
    
    PAYMENT_TYPE_CHOICES = [
        ('full', 'To\'liq to\'lov'),
        ('partial', 'Qisman to\'lov'),
        ('prepayment', 'Oldindan to\'lov'),
        ('final', 'Yakuniy to\'lov'),
        ('refund', 'Qaytarilgan to\'lov'),
    ]
    
    # YANGI: To'lov usullari
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Naqd pul'),
        ('card', 'Plastik karta'),
        ('transfer', 'Bank o\'tkazmasi'),
        ('online', 'Online to\'lov'),
        ('mobile', 'Mobil to\'lov'),
        ('installment', 'Muddatli to\'lov'),
    ]
    
    # YANGI: To'lov statuslari
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('confirmed', 'Tasdiqlangan'),
        ('cancelled', 'Bekor qilingan'),
        ('refunded', 'Qaytarilgan'),
    ]
    
    # Asosiy ma'lumotlar
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Buyurtma'
    )
    
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name='To\'lov turi'
    )
    
    # YANGI: To'lov usuli
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        verbose_name='To\'lov usuli'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Summa'
    )
    
    # YANGI: To'lov statusi
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    
    # To'lov sanalari
    payment_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='To\'lov sanasi'
    )
    
    # YANGI: Rejalashtirilgan to'lov sanasi (muddatli to'lov uchun)
    scheduled_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Rejalashtirilgan sana',
        help_text='Muddatli to\'lovlar uchun'
    )
    
    # YANGI: Chek raqami
    receipt_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Chek/Hujjat raqami',
        help_text='Bank cheki yoki boshqa hujjat raqami'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    
    # Kim qabul qildi
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_payments',
        verbose_name='Qabul qilgan'
    )
    
    # Tasdiqlash ma'lumotlari
    is_confirmed = models.BooleanField(
        default=False,
        verbose_name='Tasdiqlangan'
    )
    
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_payments',
        verbose_name='Tasdiqlagan'
    )
    
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Tasdiqlangan sana'
    )
    
    # YANGI: Qaytarilgan to'lov ma'lumotlari
    refund_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Qaytarish sababi'
    )
    
    refunded_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Qaytarilgan sana'
    )
    
    refunded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refunded_payments',
        verbose_name='Qaytargan'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='O\'zgartirilgan sana'
    )
    
    class Meta:
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['payment_date']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.amount} so'm ({self.get_payment_type_display()})"
    
    def save(self, *args, **kwargs):
        """YANGI: Avtomatik tasdiqlash va sana o'rnatish"""
        if self.is_confirmed and not self.confirmed_at:
            from django.utils import timezone
            self.confirmed_at = timezone.now()
            self.status = 'confirmed'
        
        if self.status == 'refunded' and not self.refunded_at:
            from django.utils import timezone
            self.refunded_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def is_partial_payment(self):
        """YANGI: Qisman to'lov ekanligini tekshirish"""
        return self.payment_type == 'partial'
    
    def get_payment_method_icon(self):
        """YANGI: To'lov usuli uchun icon"""
        icons = {
            'cash': 'bi-cash',
            'card': 'bi-credit-card',
            'transfer': 'bi-bank',
            'online': 'bi-globe',
            'mobile': 'bi-phone',
            'installment': 'bi-calendar3',
        }
        return icons.get(self.payment_method, 'bi-cash')
    
    def get_status_badge_class(self):
        """YANGI: Status uchun badge rangi"""
        classes = {
            'pending': 'badge bg-warning text-dark',
            'confirmed': 'badge bg-success',
            'cancelled': 'badge bg-danger',
            'refunded': 'badge bg-info',
        }
        return classes.get(self.status, 'badge bg-secondary')


class PaymentPlan(models.Model):
    """
    YANGI: Muddatli to'lov rejasi
    """
    
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payment_plan',
        verbose_name='Buyurtma'
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Umumiy summa'
    )
    
    down_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='Oldindan to\'lov'
    )
    
    monthly_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Oylik to\'lov'
    )
    
    duration_months = models.PositiveIntegerField(
        verbose_name='Muddati (oy)'
    )
    
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='Foiz stavkasi (%)',
        help_text='Yillik foiz stavkasi'
    )
    
    start_date = models.DateField(
        verbose_name='Boshlanish sanasi'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana'
    )
    
    class Meta:
        verbose_name = 'To\'lov rejasi'
        verbose_name_plural = 'To\'lov rejalari'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.duration_months} oy"
    
    def remaining_amount(self):
        """Qolgan to'lov summasi"""
        paid_amount = self.order.payments.filter(
            status='confirmed'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        return max(Decimal('0'), self.total_amount - paid_amount)
    
    def next_payment_date(self):
        """Keyingi to'lov sanasi"""
        from dateutil.relativedelta import relativedelta
        
        paid_count = self.order.payments.filter(
            status='confirmed',
            payment_type__in=['partial', 'final']
        ).count()
        
        if paid_count >= self.duration_months:
            return None
        
        return self.start_date + relativedelta(months=paid_count + 1)
    
    def is_completed(self):
        """To'lov rejasi tugatilgan ekanligini tekshirish"""
        return self.remaining_amount() <= Decimal('0')