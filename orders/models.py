# orders/models.py - YANGILANGAN VERSIYA ("new" status olib tashlandi)

from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from customers.models import Customer
from accounts.models import User
from decimal import Decimal
import uuid

class Order(models.Model):
    """Buyurtma modeli - GPS koordinatalar bilan"""
    
    STATUS_CHOICES = [
        ('measuring', 'O\'lchovda'),      # O'lchov olish kerak
        ('processing', 'Ishlanmoqda'),   # Ishlab chiqarish jarayonida
        ('installing', 'O\'rnatilmoqda'), # O'rnatish jarayonida  
        ('installed', 'O\'rnatildi'),     # Tugallangan
        ('cancelled', 'Bekor qilindi'),  # Bekor qilingan
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'To\'lanmagan'),
        ('partial', 'Qisman to\'langan'),
        ('paid', 'To\'liq to\'langan'),
        ('overpaid', 'Ortiqcha to\'langan'),
    ]
    
    # Asosiy maydonlar
    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Buyurtma raqami'
    )
    
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Mijoz'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='measuring',  # Yangi buyurtma darhol o'lchovga boradi
        verbose_name='Holat'
    )
    
    address = models.TextField(
        verbose_name='O\'lchov manzili',
        help_text='Jalyuzi o\'rnatilishi kerak bo\'lgan aniq manzil'
    )
    
    # ✅ GPS KOORDINATALAR - YANGI FIELDLAR
    measurement_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='O\'lchov joyi kenglik (Latitude)',
        help_text='GPS koordinat - kenglik (-90 dan +90 gacha)'
    )
    
    measurement_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='O\'lchov joyi uzunlik (Longitude)',
        help_text='GPS koordinat - uzunlik (-180 dan +180 gacha)'
    )
    
    measurement_location_accuracy = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='GPS aniqlik',
        help_text='GPS aniqlik darajasi (metrlarda)'
    )
    
    # Narx va to'lov
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
    
    # Texnik xodimlar tayinlanishi
    assigned_measurer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_measuring_orders',
        limit_choices_to={'role': 'technical', 'can_measure': True},
        verbose_name='Tayinlangan o\'lchov oluvchi'
    )
    
    assigned_manufacturer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_manufacturing_orders',
        limit_choices_to={'role': 'technical', 'can_manufacture': True},
        verbose_name='Tayinlangan ishlab chiqaruvchi'
    )
    
    assigned_installer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_installation_orders',
        limit_choices_to={'role': 'technical', 'can_install': True},
        verbose_name='Tayinlangan o\'rnatuvchi'
    )
    
    # Jarayon sanalari
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
        verbose_name='Ishlab chiqarish boshlanish sanasi'
    )
    production_completed_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Ishlab chiqarish yakunlanish sanasi'
    )
    installation_completed_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='O\'rnatish yakunlanish sanasi'
    )
    
    # Qo'shimcha ma'lumotlar
    notes = models.TextField(
        blank=True,
        verbose_name='Izohlar'
    )
    measurement_notes = models.TextField(
        blank=True,
        verbose_name='O\'lchov ishi izohlari'
    )
    
    # Tizim sanalari
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
    
    def __str__(self):
        return f"#{self.order_number} - {self.customer.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Order number yaratish
        if not self.order_number:
            last_order = Order.objects.order_by('-id').first()
            if last_order and last_order.order_number:
                try:
                    last_number = int(last_order.order_number)
                    self.order_number = str(last_number + 1).zfill(6)
                except ValueError:
                    self.order_number = "000001"
            else:
                self.order_number = "000001"
        
        # To'lov statusini yangilash
        if self.total_amount > 0:
            if self.paid_amount == 0:
                self.payment_status = 'pending'
            elif self.paid_amount < self.total_amount:
                self.payment_status = 'partial'
            elif self.paid_amount == self.total_amount:
                self.payment_status = 'paid'
            else:
                self.payment_status = 'overpaid'
        
        super().save(*args, **kwargs)
    
    @property
    def remaining_amount(self):
        """Qolgan to'lov summasi"""
        return max(self.total_amount - self.paid_amount, Decimal('0'))
    
    @property
    def progress_percentage(self):
        """Buyurtma jarayonining foizi"""
        status_weights = {
            'measuring': 20,
            'processing': 50,
            'installing': 80,
            'installed': 100,
            'cancelled': 0
        }
        return status_weights.get(self.status, 0)

    @property
    def has_gps_location(self):
        """GPS koordinatlar mavjudligini tekshirish"""
        return self.measurement_latitude is not None and self.measurement_longitude is not None
    
    @property
    def google_maps_url(self):
        """Google Maps URL yaratish"""
        if self.has_gps_location:
            return f"https://www.google.com/maps?q={self.measurement_latitude},{self.measurement_longitude}&z=18"
        return None
    
    @property
    def yandex_maps_url(self):
        """Yandex Maps URL yaratish (O'zbekiston uchun)"""
        if self.has_gps_location:
            return f"https://yandex.uz/maps/?ll={self.measurement_longitude},{self.measurement_latitude}&z=18&pt={self.measurement_longitude},{self.measurement_latitude}"
        return None
    
    def get_location_display(self):
        """GPS koordinatlarni chiroyli ko'rinishda qaytarish"""
        if self.has_gps_location:
            lat_dir = "S" if float(self.measurement_latitude) < 0 else "S"
            lng_dir = "G" if float(self.measurement_longitude) < 0 else "S"
            return f"{abs(float(self.measurement_latitude)):.6f}°{lat_dir}, {abs(float(self.measurement_longitude)):.6f}°{lng_dir}"
        return "GPS ma'lumot yo'q"

    def update_payment_status(self):
        """To'lov statusini yangilash"""
        if self.total_amount > 0:
            if self.paid_amount == 0:
                self.payment_status = 'pending'
            elif self.paid_amount < self.total_amount:
                self.payment_status = 'partial'
            elif self.paid_amount == self.total_amount:
                self.payment_status = 'paid'
            else:
                self.payment_status = 'overpaid'
        else:
            self.payment_status = 'pending'

class OrderItem(models.Model):
    """
    Buyurtma elementlari (Jalyuzilar)
    """
    
    BLIND_TYPE_CHOICES = [
        ('horizontal', 'Gorizontal jalyuzi'),
        ('vertical', 'Vertikal jalyuzi'),
        ('roller', 'Rollo parda'),
        ('pleated', 'Plisse parda'),
        ('bamboo', 'Bambuk jalyuzi'),
        ('wooden', 'Yog\'och jalyuzi'),
        ('fabric', 'Mato jalyuzi'),
    ]
    
    MATERIAL_CHOICES = [
        ('aluminum', 'Alyuminiy'),
        ('plastic', 'Plastik'),
        ('wood', 'Yog\'och'),
        ('fabric', 'Mato'),
        ('bamboo', 'Bambuk'),
        ('composite', 'Kompozit'),
    ]
    
    INSTALLATION_TYPE_CHOICES = [
        ('wall', 'Devorga o\'rnatish'),
        ('ceiling', 'Shiftga o\'rnatish'),
        ('window_frame', 'Deraza romiga o\'rnatish'),
        ('niche', 'Ichki o\'rnatish'),
    ]
    
    MECHANISM_CHOICES = [
        ('cord', 'Ip bilan boshqarish'),
        ('chain', 'Zanjir bilan boshqarish'),
        ('wand', 'Tayoqcha bilan boshqarish'),
        ('motorized', 'Elektr motor'),
        ('remote', 'Masofadan boshqarish'),
        ('smart', 'Aqlli boshqarish'),
    ]
    
    CORNICE_TYPE_CHOICES = [
        ('standard', 'Standart karniz'),
        ('decorative', 'Dekorativ karniz'),
        ('hidden', 'Yashirin karniz'),
        ('box', 'Quti karniz'),
        ('double', 'Ikki qatorli karniz'),
    ]
    
    # Bog'lanishlar
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Buyurtma'
    )
    
    # Jalyuzi ma'lumotlari
    blind_type = models.CharField(
        max_length=20,
        choices=BLIND_TYPE_CHOICES,
        verbose_name='Jalyuzi turi'
    )
    
    # O'lchamlar (santimetr)
    width = models.PositiveIntegerField(
        validators=[MinValueValidator(10)],
        verbose_name='Eni (sm)'
    )
    height = models.PositiveIntegerField(
        validators=[MinValueValidator(10)],
        verbose_name='Bo\'yi (sm)'
    )
    
    # Material va texnik ma'lumotlar
    material = models.CharField(
        max_length=20,
        choices=MATERIAL_CHOICES,
        verbose_name='Material'
    )
    
    installation_type = models.CharField(
        max_length=20,
        choices=INSTALLATION_TYPE_CHOICES,
        verbose_name='O\'rnatish turi'
    )
    
    mechanism = models.CharField(
        max_length=20,
        choices=MECHANISM_CHOICES,
        verbose_name='Mexanizm turi'
    )
    
    cornice_type = models.CharField(
        max_length=20,
        choices=CORNICE_TYPE_CHOICES,
        verbose_name='Karniz turi'
    )
    
    # Narx ma'lumotlari
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Donasi'
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Birlik narxi'
    )
    
    # Hisoblangan ma'lumotlar
    @property
    def area(self):
        """Maydon (m²)"""
        return Decimal(str(self.width * self.height / 10000))
    
    @property
    def total_price(self):
        """Umumiy narx"""
        return self.unit_price * self.quantity
    
    # Qo'shimcha ma'lumotlar
    room_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Xona nomi'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='Qo\'shimcha izohlar'
    )
    
    # Tizim sanalari
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Yangilangan sana'
    )
    
    class Meta:
        verbose_name = 'Buyurtma elementi'
        verbose_name_plural = 'Buyurtma elementlari'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.get_blind_type_display()} - {self.width}x{self.height}sm"