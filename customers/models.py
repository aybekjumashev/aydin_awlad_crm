# customers/models.py

from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
import uuid


class Customer(models.Model):
    """
    Mijozlar modeli - Yangilangan versiya
    """
    
    # Asosiy ma'lumotlar
    first_name = models.CharField(
        max_length=50,
        verbose_name='Ism'
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name='Familiya'
    )
    
    # Tug'ilgan kun (yangi maydon)
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Tug\'ilgan kun'
    )
    
    # Asosiy telefon raqam (eski uchun)
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
    
    # Mijoz uchun maxsus identifikator (public sahifa uchun)
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
        """Yoshni hisoblash"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None


class CustomerPhone(models.Model):
    """
    Mijozning telefon raqamlari - Ko'p telefon raqam uchun
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
        related_name='phone_numbers',
        verbose_name='Mijoz'
    )
    
    phone = models.CharField(
        max_length=15,
        verbose_name='Telefon raqam',
        validators=[
            RegexValidator(
                regex=r'^\+998\d{9}$',
                message='Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak'
            )
        ]
    )
    
    phone_type = models.CharField(
        max_length=10,
        choices=PHONE_TYPE_CHOICES,
        default='mobile',
        verbose_name='Telefon turi'
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Asosiy raqam'
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
        ordering = ['-is_primary', '-created_at']
        unique_together = ['customer', 'phone']
    
    def __str__(self):
        primary_text = " (Asosiy)" if self.is_primary else ""
        return f"{self.phone} - {self.get_phone_type_display()}{primary_text}"
    
    def save(self, *args, **kwargs):
        # Agar bu asosiy raqam bo'lsa, boshqa asosiy raqamlarni o'chirish
        if self.is_primary:
            CustomerPhone.objects.filter(
                customer=self.customer,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)