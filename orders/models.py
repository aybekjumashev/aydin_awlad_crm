# orders/models.py - YANGILANGAN VERSIYA

from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from customers.models import Customer
from accounts.models import User
from decimal import Decimal
import uuid


class Order(models.Model):
    """
    Buyurtmalar modeli - Yangilangan versiya
    """
    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('measuring', 'O\'lchovda'),
        ('processing', 'Ishlanmoqda'),
        ('installing', 'O\'rnatilmoqda'),  # YANGI STATUS
        ('installed', 'O\'rnatildi'),
        ('cancelled', 'Bekor qilindi'),
    ]
    
    # To'lov holatlari
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'To\'lanmagan'),
        ('partial', 'Qisman to\'langan'),
        ('paid', 'To\'liq to\'langan'),
        ('overpaid', 'Ortiqcha to\'langan'),
    ]
    
    # Asosiy ma'lumotlar
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Mijoz'
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Buyurtma raqami'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='measuring',  # Yangi buyurtma darhol o'lchovga yuboriladi
        verbose_name='Holat'
    )
    
    # Manzil ma'lumotlari
    address = models.TextField(
        verbose_name='O\'lchov manzili',
        help_text='Jalyuzi o\'rnatilishi kerak bo\'lgan aniq manzil'
    )
    
    # To'lov ma'lumotlari - YANGI
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Umumiy narx'
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='To\'langan summa'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='To\'lov holati'
    )
    
    # Texnik xodimlar tayinlanishi - YANGI
    assigned_measurer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_measurements',
        limit_choices_to={'role': 'technical', 'can_measure': True},
        verbose_name='O\'lchov oluvchi'
    )
    assigned_manufacturer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_manufacturing',
        limit_choices_to={'role': 'technical', 'can_manufacture': True},
        verbose_name='Ishlab chiquvchi'
    )
    assigned_installer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_installations',
        limit_choices_to={'role': 'technical', 'can_install': True},
        verbose_name='O\'rnatuvchi'
    )
    
    # Sanalar
    measurement_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='O\'lchov sanasi'
    )
    measurement_completed_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='O\'lchov yakunlangan sana'
    )
    production_start_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Ishlab chiqarish boshlangan sana'
    )
    production_completed_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Ishlab chiqarish yakunlangan sana'
    )
    installation_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='O\'rnatish sanasi'
    )
    installation_completed_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='O\'rnatish yakunlangan sana'
    )
    
    # Izohlar
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Umumiy izohlar'
    )
    measurement_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='O\'lchov izohlari'
    )
    production_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Ishlab chiqarish izohlari'
    )
    installation_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='O\'rnatish izohlari'
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
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Buyurtma raqamini avtomatik yaratish
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # To'lov holatini yangilash
        self.update_payment_status()
        
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Buyurtma raqamini yaratish"""
        import datetime
        today = datetime.date.today()
        prefix = f"AA{today.strftime('%Y%m%d')}"
        
        # Bugungi oxirgi buyurtma raqamini topish
        last_order = Order.objects.filter(
            order_number__startswith=prefix
        ).order_by('-order_number').first()
        
        if last_order:
            # Oxirgi raqamdan keyingisini yaratish
            last_number = int(last_order.order_number[-3:])
            new_number = f"{prefix}{last_number + 1:03d}"
        else:
            # Birinchi buyurtma
            new_number = f"{prefix}001"
        
        return new_number
    
    def update_payment_status(self):
        """To'lov holatini yangilash"""
        if self.paid_amount <= 0:
            self.payment_status = 'pending'
        elif self.paid_amount >= self.total_amount:
            if self.paid_amount > self.total_amount:
                self.payment_status = 'overpaid'
            else:
                self.payment_status = 'paid'
        else:
            self.payment_status = 'partial'
    
    @property
    def remaining_amount(self):
        """Qolgan qarzdorlik"""
        return max(self.total_amount - self.paid_amount, Decimal('0'))
    
    @property
    def total_area(self):
        """Umumiy maydon (m²)"""
        total = Decimal('0')
        for item in self.items.all():
            total += item.area
        return total
    
    def get_absolute_url(self):
        return reverse('orders:detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        return f"#{self.order_number} - {self.customer.full_name}"


class OrderItem(models.Model):
    """
    Buyurtma elementlari (Jalyuzilar) - YANGILANGAN
    """
    
    BLIND_TYPE_CHOICES = [
        ('horizontal', 'Gorizontal jalyuzi'),
        ('vertical', 'Vertikal jalyuzi'),
        ('roller', 'Rulon parda'),
        ('roman', 'Rim parda'),
        ('plisse', 'Plisse parda'),
        ('zebra', 'Zebra parda'),  # YANGI
        ('day_night', 'Kun-tun parda'),  # YANGI
    ]
    
    MATERIAL_CHOICES = [
        ('aluminum', 'Alyuminiy'),
        ('pvc', 'PVC'),
        ('wood', 'Yog\'och'),
        ('fabric', 'Mato'),
        ('bamboo', 'Bambuk'),
        ('polyester', 'Polyester'),  # YANGI
        ('blackout', 'Blackout'),  # YANGI
    ]
    
    INSTALLATION_TYPE_CHOICES = [
        ('ceiling', 'Shiftga'),
        ('wall', 'Devorga'),
        ('window_frame', 'Deraza romiga'),
        ('niche', 'Tokchaga'),
    ]
    
    MECHANISM_CHOICES = [
        ('cord', 'Ip bilan'),
        ('chain', 'Zanjir bilan'),
        ('motor', 'Elektr motor'),
        ('remote', 'Masofadan boshqarish'),
        ('manual', 'Qo\'lda'),
    ]
    
    CORNICE_TYPE_CHOICES = [
        ('standard', 'Standart'),
        ('decorative', 'Dekorativ'),
        ('hidden', 'Yashirin'),
        ('ceiling_mount', 'Shiftga o\'rnatilgan'),
    ]
    
    # Bog'lanish
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Buyurtma'
    )
    
    # Jalyuzi turlari va xususiyatlari
    blind_type = models.CharField(
        max_length=20,
        choices=BLIND_TYPE_CHOICES,
        verbose_name='Jalyuzi turi'
    )
    
    # O'lchamlar
    width = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Eni (sm)',
        help_text='Santimetrda'
    )
    height = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Bo\'yi (sm)',
        help_text='Santimetrda'
    )
    
    # Material va o'rnatish
    material = models.CharField(
        max_length=20,
        choices=MATERIAL_CHOICES,
        verbose_name='Material turi'
    )
    installation_type = models.CharField(
        max_length=20,
        choices=INSTALLATION_TYPE_CHOICES,
        verbose_name='O\'rnatish turi'
    )
    mechanism = models.CharField(
        max_length=20,
        choices=MECHANISM_CHOICES,
        default='cord',
        verbose_name='Mexanizm turi'
    )
    cornice_type = models.CharField(
        max_length=20,
        choices=CORNICE_TYPE_CHOICES,
        default='standard',
        verbose_name='Karniz turi'
    )
    
    # Qo'shimcha ma'lumotlar
    room_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Xona nomi',
        help_text='Masalan: Yotoq xona, Mehmonxona'
    )
    color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Rang'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Qo\'shimcha izoh'
    )
    
    # Narx va miqdor
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Donasi'
    )
    unit_price_per_sqm = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Birlik narxi (m² uchun)',
        help_text='1 kvadrat metr uchun narx so\'mda'
    )
    unit_price_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Birlik narxi (so\'m)',
        help_text='Bir dona jalyuzi uchun umumiy narx'
    )
    
    class Meta:
        verbose_name = 'Buyurtma elementi'
        verbose_name_plural = 'Buyurtma elementlari'
        ordering = ['id']
    
    @property
    def area(self):
        """Maydon m² da"""
        return (self.width * self.height / 10000) * self.quantity  # sm -> m²
    
    @property
    def total_price(self):
        """Umumiy narx"""
        if self.unit_price_total > 0:
            return self.unit_price_total * self.quantity
        else:
            return self.unit_price_per_sqm * self.area
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Buyurtmaning umumiy narxini yangilash
        self.order.total_amount = sum(item.total_price for item in self.order.items.all())
        self.order.update_payment_status()
        self.order.save(update_fields=['total_amount', 'payment_status'])
    
    def __str__(self):
        return f"{self.get_blind_type_display()} - {self.room_name or 'Xona'}"