# payments/models.py - YANGILANGAN VERSIYA

from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal
from django.utils import timezone


class Payment(models.Model):
    """
    To'lovlar modeli - To'liq yangilangan versiya
    """
    
    PAYMENT_TYPE_CHOICES = [
        ('prepayment', 'Oldindan to\'lov'),
        ('partial', 'Qisman to\'lov'),
        ('final', 'Yakuniy to\'lov'),
        ('full', 'To\'liq to\'lov'),
        ('refund', 'Qaytarilgan to\'lov'),
        ('discount', 'Chegirma'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Naqd pul'),
        ('card', 'Plastik karta'),
        ('transfer', 'Bank o\'tkazmasi'),
        ('mobile', 'Mobil to\'lov'),
        ('online', 'Online to\'lov'),
        ('installment', 'Muddatli to\'lov'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('confirmed', 'Tasdiqlangan'),
        ('cancelled', 'Bekor qilingan'),
        ('refunded', 'Qaytarilgan'),
    ]
    
    # Asosiy bog'lanishlar
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Buyurtma'
    )
    
    # To'lov ma'lumotlari
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name='To\'lov turi'
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        verbose_name='To\'lov usuli'
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Summa'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    
    # Sanalar
    payment_date = models.DateTimeField(
        verbose_name='To\'lov sanasi',
        help_text='To\'lov amalga oshirilgan sana'
    )
    
    scheduled_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Rejalashtirilgan sana',
        help_text='Muddatli to\'lov uchun'
    )
    
    confirmed_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Tasdiqlangan sana'
    )
    
    # Kim tomonidan qabul qilingan
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='received_payments',
        verbose_name='Qabul qilgan xodim'
    )
    
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='confirmed_payments',
        verbose_name='Tasdiqlagan xodim'
    )
    
    # Qo'shimcha ma'lumotlar
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Ma\'lumotnoma raqami',
        help_text='Bank o\'tkazmasi yoki karta to\'lovi uchun'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izohlar'
    )
    
    # Qaytarilgan to'lov uchun
    refund_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Qaytarish sababi'
    )
    
    refunded_to_payment = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Qaysi to\'lovga qaytarilgan'
    )
    
    # Avtomatik sanalar
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Yangilangan sana'
    )
    
    class Meta:
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'
        ordering = ['-payment_date']
    
    def save(self, *args, **kwargs):
        # To'lov tasdiqlanganida sanani belgilash
        if self.status == 'confirmed' and not self.confirmed_date:
            from django.utils import timezone
            self.confirmed_date = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Buyurtmaning to'lov holatini yangilash
        self.order.update_payment_status()
        self.order.save(update_fields=['paid_amount', 'payment_status'])
    
    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        # To'lov o'chirilgandan keyin buyurtma holatini yangilash
        order.update_payment_status()
        order.save(update_fields=['paid_amount', 'payment_status'])
    
    @property
    def is_confirmed(self):
        """To'lov tasdiqlangan mi?"""
        return self.status == 'confirmed'
    
    @property
    def is_refund(self):
        """Bu qaytarilgan to'lovmi?"""
        return self.payment_type == 'refund'
    
    def confirm_payment(self, user):
        """To'lovni tasdiqlash"""
        self.status = 'confirmed'
        self.confirmed_by = user
        from django.utils import timezone
        self.confirmed_date = timezone.now()
        self.save()
    
    def cancel_payment(self, reason=""):
        """To'lovni bekor qilish"""
        self.status = 'cancelled'
        if reason:
            self.notes = f"{self.notes or ''}\nBekor qilish sababi: {reason}".strip()
        self.save()
    
    def create_refund(self, amount, reason, user):
        """Qaytarilgan to'lov yaratish"""
        refund = Payment.objects.create(
            order=self.order,
            payment_type='refund',
            payment_method=self.payment_method,
            amount=amount,
            status='confirmed',
            payment_date=timezone.now(),
            confirmed_date=timezone.now(),
            received_by=user,
            confirmed_by=user,
            refund_reason=reason,
            refunded_to_payment=self,
            notes=f"#{self.id} raqamli to'lovga qaytarildi"
        )
        return refund
    
    def __str__(self):
        return f"#{self.order.order_number} - {self.amount:,.0f} so'm ({self.get_payment_type_display()})"


class PaymentSchedule(models.Model):
    """
    Muddatli to'lov rejasi
    """
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payment_schedules',
        verbose_name='Buyurtma'
    )
    
    installment_number = models.PositiveIntegerField(
        verbose_name='To\'lov tartib raqami',
        help_text='1-chi to\'lov, 2-chi to\'lov va h.k.'
    )
    
    scheduled_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Rejalashtirilgan summa'
    )
    
    due_date = models.DateField(
        verbose_name='Muddati'
    )
    
    is_paid = models.BooleanField(
        default=False,
        verbose_name='To\'langan'
    )
    
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='schedule',
        verbose_name='To\'lov'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izohlar'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana'
    )
    
    class Meta:
        verbose_name = 'To\'lov rejasi'
        verbose_name_plural = 'To\'lov rejalari'
        ordering = ['due_date', 'installment_number']
        unique_together = ['order', 'installment_number']
    
    @property
    def is_overdue(self):
        """Muddati o'tganmi?"""
        from django.utils import timezone
        return not self.is_paid and self.due_date < timezone.now().date()
    
    @property
    def days_until_due(self):
        """Muddatgacha qancha kun qolgan"""
        from django.utils import timezone
        delta = self.due_date - timezone.now().date()
        return delta.days
    
    def mark_as_paid(self, payment):
        """To'langani belgilash"""
        self.is_paid = True
        self.payment = payment
        self.save()
    
    def __str__(self):
        return f"#{self.order.order_number} - {self.installment_number}-to'lov ({self.scheduled_amount:,.0f} so'm)"