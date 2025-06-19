# orders/models.py

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
        ('installed', 'O\'rnatildi'),
        ('cancelled', 'Bekor qilindi'),
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
        default='measuring',
        verbose_name='Holat'
    )
    
    # Manzil ma'lumotlari
    address = models.TextField(
        verbose_name='O\'lchov manzili',
        help_text='Jalyuzi o\'rnatilishi kerak bo\'lgan aniq manzil'
    )
    
    # Geoposition ma'lumotlari (yangi)
    latitude = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Kenglik (Latitude)',
        help_text='GPS koordinata - kenglik'
    )
    longitude = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Uzunlik (Longitude)',
        help_text='GPS koordinata - uzunlik'
    )
    location_accuracy = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Joylashuv aniqligi (m)',
        help_text='GPS aniqligi metrda'
    )
    
    # O'lchov ma'lumotlari
    measurement_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='O\'lchov sanasi'
    )
    measurement_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='O\'lchov izohlari'
    )
    
    # Ishlab chiqarish ma'lumotlari
    production_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Ishlab chiqarish sanasi'
    )
    production_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Ishlab chiqarish izohlari'
    )
    
    # O'rnatish ma'lumotlari
    installation_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='O\'rnatish sanasi'
    )
    installation_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='O\'rnatish izohlari'
    )
    
    # Umumiy izohlar
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Qo\'shimcha izoh'
    )
    
    # Kim yaratdi va o'zgartirdi
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_orders',
        verbose_name='Yaratuvchi'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_orders',
        verbose_name='O\'zgartiruvchi'
    )
    
    # Jarayon mas'ullari
    measured_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='measured_orders',
        verbose_name='O\'lchov olgan'
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_orders',
        verbose_name='Ishlab chiqargan'
    )
    installed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installed_orders',
        verbose_name='O\'rnatgan'
    )
    
    # Vaqt belgilari
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='O\'zgartirilgan sana'
    )
    
    class Meta:
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.get_full_name()}"
    
    def get_absolute_url(self):
        """Buyurtma sahifasiga havola"""
        return reverse('orders:detail', kwargs={'pk': self.pk})
    
    def total_items(self):
        """Umumiy jalyuzi donasi"""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    def total_area(self):
        """Umumiy maydon (m²)"""
        total = Decimal('0')
        for item in self.items.all():
            total += item.total_area()
        return total
    
    def total_price(self):
        """Umumiy narx"""
        total = Decimal('0')
        for item in self.items.all():
            total += item.total_price()
        return total
    
    def total_paid(self):
        """To'langan summa"""
        return self.payments.filter(
            is_confirmed=True
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
    
    def remaining_debt(self):
        """Qolgan qarzdorlik"""
        return max(Decimal('0'), self.total_price() - self.total_paid())
    
    def is_fully_paid(self):
        """To'liq to'langanmi"""
        return self.remaining_debt() == 0
    
    def payment_percentage(self):
        """To'lov foizi"""
        total = self.total_price()
        if total > 0:
            return (self.total_paid() / total) * 100
        return 0
    
    def get_google_maps_url(self):
        """Google Maps havolasi"""
        if self.latitude and self.longitude:
            return f"https://maps.google.com/maps?q={self.latitude},{self.longitude}"
        return None
    
    def save(self, *args, **kwargs):
        # Buyurtma raqamini avtomatik yaratish
        if not self.order_number:
            from django.utils import timezone
            now = timezone.now()
            last_order = Order.objects.filter(
                created_at__year=now.year,
                created_at__month=now.month
            ).order_by('-created_at').first()
            
            if last_order and last_order.order_number:
                try:
                    last_number = int(last_order.order_number.split('-')[-1])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
            
            self.order_number = f"AA-{now.year}-{now.month:02d}-{next_number:04d}"
        
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Buyurtma elementlari - Yangilangan versiya
    """
    
    BLIND_TYPE_CHOICES = [
        ('horizontal', 'Gorizontal'),
        ('vertical', 'Vertikal'),
        ('roller', 'Rulon'),
        ('roman', 'Rim'),
        ('pleated', 'Plisse'),
        ('wooden', 'Yog\'och'),
        ('aluminum', 'Alyuminiy'),
    ]
    
    MATERIAL_CHOICES = [
        ('aluminum', 'Alyuminiy'),
        ('pvc', 'PVC'),
        ('wood', 'Yog\'och'),
        ('fabric', 'Mato'),
        ('bamboo', 'Bambuk'),
        ('metal', 'Metall'),
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
    
    # Miqdor va narx
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Donasi'
    )
    
    # Yangi narx maydonlari
    unit_price_per_sqm = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Birlik narxi (m² uchun)',
        help_text='1 kvadrat metr uchun narx so\'mda',
        default=Decimal('0')
    )
    
    unit_price_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Birlik narxi (so\'m)',
        help_text='Bir dona uchun umumiy narx',
        default=Decimal('0')
    )
    
    # Vaqt belgilari
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='O\'zgartirilgan sana'
    )
    
    class Meta:
        verbose_name = 'Buyurtma elementi'
        verbose_name_plural = 'Buyurtma elementlari'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_blind_type_display()} - {self.width}x{self.height}sm"
    
    def area_sqm(self):
        """Maydon kvadrat metrda"""
        width_m = self.width / 100  # sm dan m ga
        height_m = self.height / 100  # sm dan m ga
        return round(width_m * height_m, 4)
    
    def total_area(self):
        """Umumiy maydon (barcha donalar uchun)"""
        return Decimal(str(self.area_sqm())) * self.quantity
    
    def calculate_price_from_sqm(self):
        """m² narxidan umumiy narxni hisoblash"""
        area = Decimal(str(self.area_sqm()))
        return area * self.unit_price_per_sqm
    
    def total_price(self):
        """Umumiy narx (barcha donalar uchun)"""
        if self.unit_price_total > 0:
            # Agar birlik narxi mavjud bo'lsa
            return self.unit_price_total * self.quantity
        else:
            # m² narxidan hisoblash
            return self.calculate_price_from_sqm() * self.quantity
    
    def save(self, *args, **kwargs):
        # Agar unit_price_per_sqm berilgan bo'lsa, unit_price_total ni avtomatik hisoblash
        if self.unit_price_per_sqm > 0 and self.unit_price_total == 0:
            self.unit_price_total = self.calculate_price_from_sqm()
        
        # Agar unit_price_total berilgan bo'lsa, unit_price_per_sqm ni hisoblash
        elif self.unit_price_total > 0 and self.unit_price_per_sqm == 0:
            area = Decimal(str(self.area_sqm()))
            if area > 0:
                self.unit_price_per_sqm = self.unit_price_total / area
        
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    Buyurtma holati tarixi
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Buyurtma'
    )
    
    old_status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name='Oldingi holat'
    )
    
    new_status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        verbose_name='Yangi holat'
    )
    
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='O\'zgartiruvchi'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='O\'zgartirilgan vaqt'
    )
    
    class Meta:
        verbose_name = 'Holat tarixi'
        verbose_name_plural = 'Holat tarixlari'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} -> {self.new_status}"