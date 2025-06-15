# orders/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from customers.models import Customer
from accounts.models import User
from decimal import Decimal


class Order(models.Model):
    """
    Buyurtmalar modeli - Asosiy buyurtma ma'lumotlari
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
    
    # Qo'shimcha ma'lumotlar
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
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_orders',
        verbose_name='Bekor qilgan'
    )
    
    # Avans to'lovi (legacy - endi payments app da)
    advance_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Avans to\'lovi'
    )
    advance_payment_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Avans to\'lovi sanasi'
    )
    advance_payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Naqd pul'),
            ('card', 'Plastik karta'),
            ('bank_transfer', 'Bank o\'tkazmasi'),
            ('click', 'Click'),
            ('payme', 'Payme'),
            ('uzcard', 'UzCard'),
            ('humo', 'Humo'),
        ],
        blank=True,
        null=True,
        verbose_name='Avans to\'lov usuli'
    )
    
    # Sanalar
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Yaratilgan sana'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='O\'zgartirilgan sana'
    )
    measurement_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='O\'lchov sanasi'
    )
    processing_start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Ishlab chiqarish boshlangan sana'
    )
    installation_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='O\'rnatish sanasi'
    )
    cancelled_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Bekor qilingan sana'
    )
    
    # Bekor qilish sababi
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Bekor qilish sababi'
    )
    
    class Meta:
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"#{self.order_number} - {self.customer.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Saqlashda avtomatik order_number yaratish"""
        if not self.order_number:
            import datetime
            today = datetime.date.today()
            count = Order.objects.filter(created_at__date=today).count() + 1
            self.order_number = f"AYD{today.strftime('%Y%m%d')}{count:03d}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('orders:detail', kwargs={'pk': self.pk})
    
    def total_items(self):
        """Jami buyurtma elementlari soni"""
        return self.items.count()
    
    def total_quantity(self):
        """Jami donalar soni"""
        return sum(item.quantity for item in self.items.all())
    
    def total_price(self):
        """Umumiy narx"""
        return sum(item.total_price() for item in self.items.all())
    
    def total_area_sqm(self):
        """Jami maydon (kv.m)"""
        return sum(item.total_area_sqm() for item in self.items.all())
    
    def has_items(self):
        """Elementlari bor ekanligini tekshirish"""
        return self.items.exists()
    
    def get_items_summary(self):
        """Qisqa xulosangiz"""
        if not self.has_items():
            return "Hozircha jalyuzilar qo'shilmagan"
        
        types = {}
        for item in self.items.all():
            blind_type = item.get_blind_type_display()
            types[blind_type] = types.get(blind_type, 0) + item.quantity
        
        summary = ", ".join([f"{name}: {count} dona" for name, count in types.items()])
        return summary
    
    def total_paid(self):
        """Jami to'langan miqdor"""
        return sum(
            payment.amount for payment in self.payments.filter(is_confirmed=True)
        )
    
    def total_advance_paid(self):
        """Jami avans to'lovlari"""
        return sum(
            payment.amount for payment in self.payments.filter(
                payment_type='advance', 
                is_confirmed=True
            )
        )
    
    def remaining_balance(self):
        """Qoldiq to'lov"""
        return max(self.total_price() - self.total_paid(), 0)
    
    def is_fully_paid(self):
        """To'liq to'langan ekanligini tekshirish"""
        return self.remaining_balance() == 0
    
    def payment_percentage(self):
        """To'lov foizi"""
        total = self.total_price()
        if total > 0:
            return (self.total_paid() / total) * 100
        return 0
    
    def get_payment_status(self):
        """To'lov holati"""
        if self.total_paid() == 0:
            return {'status': 'not_paid', 'label': 'To\'lanmagan', 'class': 'danger'}
        elif self.is_fully_paid():
            return {'status': 'paid', 'label': 'To\'liq to\'langan', 'class': 'success'}
        else:
            return {'status': 'partial', 'label': 'Qisman to\'langan', 'class': 'warning'}
    
    def can_be_measured(self):
        """O'lchov olish mumkinligini tekshirish"""
        return self.status in ['new', 'measuring']
    
    def can_be_processed(self):
        """Ishlab chiqarish mumkinligini tekshirish"""
        return self.status in ['measuring', 'processing'] and self.has_items()
    
    def can_be_installed(self):
        """O'rnatish mumkinligini tekshirish"""
        return self.status == 'processing' and self.has_items()
    
    def can_be_cancelled(self):
        """Bekor qilish mumkinligini tekshirish"""
        return self.status not in ['installed', 'cancelled']
    
    def get_next_possible_statuses(self):
        """Keyingi mumkin bo'lgan statuslar"""
        status_flow = {
            'new': ['measuring', 'cancelled'],
            'measuring': ['processing', 'cancelled'],
            'processing': ['installed', 'cancelled'],
            'installed': [],  # Tugallangan
            'cancelled': [],  # Bekor qilingan
        }
        return status_flow.get(self.status, [])
    
    def create_history(self, action, performed_by, notes=None):
        """Tarix yozuvi yaratish"""
        OrderHistory.objects.create(
            order=self,
            action=action,
            performed_by=performed_by,
            notes=notes
        )


class OrderItem(models.Model):
    """
    Buyurtma elementi - Har bir jalyuzi turi
    """
    BLIND_TYPE_CHOICES = [
        ('horizontal', 'Gorizontal jalyuzi'),
        ('vertical', 'Vertikal jalyuzi'),
        ('roller', 'Rulon parda'),
        ('roman', 'Rim parda'),
        ('plisse', 'Plisse parda'),
    ]
    
    MATERIAL_CHOICES = [
        ('aluminum', 'Alyuminiy'),
        ('pvc', 'PVC'),
        ('wood', 'Yog\'och'),
        ('fabric', 'Mato'),
        ('bamboo', 'Bambuk'),
    ]
    
    INSTALLATION_CHOICES = [
        ('wall', 'Devorga o\'rnatish'),
        ('ceiling', 'Shiftga o\'rnatish'),
        ('window_frame', 'Deraza ramkasiga'),
        ('external', 'Tashqi o\'rnatish'),
    ]
    
    # Asosiy ma'lumotlar
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Buyurtma'
    )
    blind_type = models.CharField(
        max_length=30,
        choices=BLIND_TYPE_CHOICES,
        verbose_name='Jalyuzi turi'
    )
    
    # O'lchamlar
    width = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Eni (sm)'
    )
    height = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Bo\'yi (sm)'
    )
    
    # Material va o'rnatish
    material = models.CharField(
        max_length=20,
        choices=MATERIAL_CHOICES,
        verbose_name='Material turi'
    )
    installation_type = models.CharField(
        max_length=20,
        choices=INSTALLATION_CHOICES,
        verbose_name='O\'rnatish turi'
    )
    
    # Qo'shimcha ma'lumotlar
    mechanism_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Mexanizm turi'
    )
    cornice_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Karniz turi'
    )
    room_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Xona nomi'
    )
    
    # Miqdor va narx
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Donasi'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Birlik narxi'
    )
    
    # Qo'shimcha izoh
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    
    # Sanalar
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Qo\'shilgan sana'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='O\'zgartirilgan sana'
    )
    
    class Meta:
        verbose_name = 'Buyurtma elementi'
        verbose_name_plural = 'Buyurtma elementlari'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.get_blind_type_display()} - {self.width}x{self.height}sm ({self.quantity} dona)"
    
    def total_price(self):
        """Umumiy narx (birlik narxi * miqdor)"""
        return self.unit_price * self.quantity
    
    def area_sqm(self):
        """Maydon (kv.m)"""
        return (self.width * self.height) / 10000  # sm² dan m² ga
    
    def total_area_sqm(self):
        """Umumiy maydon (kv.m) - barcha donalar uchun"""
        return self.area_sqm() * self.quantity
    
    def price_per_sqm(self):
        """1 kv.m uchun narx"""
        area = self.area_sqm()
        if area > 0:
            return self.unit_price / area
        return Decimal('0')
    
    def get_full_description(self):
        """To'liq tavsif"""
        desc_parts = [
            self.get_blind_type_display(),
            f"{self.width}x{self.height} sm",
            self.get_material_display(),
            self.get_installation_type_display(),
        ]
        
        if self.mechanism_type:
            desc_parts.append(f"Mexanizm: {self.mechanism_type}")
        
        if self.cornice_type:
            desc_parts.append(f"Karniz: {self.cornice_type}")
        
        if self.room_name:
            desc_parts.append(f"Xona: {self.room_name}")
        
        return " | ".join(desc_parts)
    
    def get_compact_description(self):
        """Qisqa tavsif"""
        desc = f"{self.get_blind_type_display()} {self.width}x{self.height}sm"
        if self.room_name:
            desc += f" ({self.room_name})"
        return desc


class OrderHistory(models.Model):
    """
    Buyurtma tarixini saqlash - kim qachon nima qilgani
    """
    ACTION_CHOICES = [
        ('created', 'Buyurtma yaratildi'),
        ('status_changed', 'Holat o\'zgartirildi'),
        ('measured', 'O\'lchov olindi'),
        ('processing_started', 'Ishlab chiqarish boshlandi'),
        ('installed', 'O\'rnatildi'),
        ('cancelled', 'Bekor qilindi'),
        ('payment_received', 'To\'lov qabul qilindi'),
        ('updated', 'Ma\'lumotlar yangilandi'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Buyurtma'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='Harakat'
    )
    old_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Eski holat'
    )
    new_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Yangi holat'
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Bajaruvchi'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Bajarilgan vaqt'
    )
    
    class Meta:
        verbose_name = 'Buyurtma tarixi'
        verbose_name_plural = 'Buyurtma tarixi'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_action_display()} - {self.performed_by}"