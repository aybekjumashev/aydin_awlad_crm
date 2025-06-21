# orders/models.py - YANGILANGAN VERSIYA ("new" status olib tashlandi)

from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from customers.models import Customer
from accounts.models import User
from decimal import Decimal
import uuid


class Order(models.Model):
    """
    Buyurtmalar modeli - "new" status olib tashlandi
    """
    STATUS_CHOICES = [
        ('measuring', 'O\'lchovda'),
        ('processing', 'Ishlanmoqda'),
        ('installing', 'O\'rnatilmoqda'),
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
    
    # To'lov ma'lumotlari
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
        return f"#{self.order_number} - {self.customer.get_full_name()}"


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