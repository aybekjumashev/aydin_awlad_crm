# orders/models.py

from django.db import models
from django.urls import reverse
from customers.models import Customer
from accounts.models import User

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
        default='measuring',  # Default status o'lchovda
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
    
    # Avans to'lovi
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
    installation_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='O\'rnatish sanasi'
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

    # Qo'shimcha sanalar
    processing_start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Ishlab chiqarish boshlangan sana'
    )
    cancelled_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Bekor qilingan sana'
    )
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
        # Buyurtma raqamini avtomatik yaratish
        if not self.order_number:
            import datetime
            today = datetime.date.today()
            count = Order.objects.filter(created_at__date=today).count() + 1
            self.order_number = f"AYD{today.strftime('%Y%m%d')}{count:03d}"
        
        # Eski status ni saqlash (history uchun)
        old_status = None
        if self.pk:
            old_instance = Order.objects.get(pk=self.pk)
            old_status = old_instance.status
        
        super().save(*args, **kwargs)
        
        # History yaratish (status o'zgarganda)
        if old_status and old_status != self.status:
            OrderHistory.objects.create(
                order=self,
                action='status_changed',
                old_status=old_status,
                new_status=self.status,
                performed_by=self.updated_by
            )
    
    def create_history(self, action, performed_by, notes=None):
        """History yozuvi yaratish"""
        OrderHistory.objects.create(
            order=self,
            action=action,
            performed_by=performed_by,
            notes=notes
        )
    
    def get_absolute_url(self):
        return reverse('order_detail', kwargs={'pk': self.pk})
    
    def total_price(self):
        """Buyurtmaning umumiy narxi"""
        return sum([item.total_price for item in self.items.all()])
    
    def total_paid(self):
        """To'langan miqdor (barcha to'lovlar)"""
        return sum([payment.amount for payment in self.payments.all()])
    
    def remaining_balance(self):
        """Qolgan to'lov miqdori"""
        return self.total_price() - self.total_paid()
    
    def is_fully_paid(self):
        """To'liq to'langan-to'llanmagan"""
        return self.remaining_balance() <= 0
    
    def advance_payments(self):
        """Avans to'lovlari"""
        return self.payments.filter(payment_type='advance')
    
    def final_payments(self):
        """Yakuniy to'lovlar"""
        return self.payments.filter(payment_type='final')
    
    def partial_payments(self):
        """Qisman to'lovlar"""
        return self.payments.filter(payment_type='partial')
    
    def total_advance_paid(self):
        """Umumiy avans miqdori"""
        return sum([payment.amount for payment in self.advance_payments()])
    
    def has_advance_payment(self):
        """Avans to'langan-to'llanmagan"""
        return self.advance_payments().exists()
    
    def total_items(self):
        """Buyurtmadagi jalyuzilar soni"""
        return self.items.count()


class OrderItem(models.Model):
    """
    Buyurtma elementlari - har bir jalyuzi uchun
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
    
    INSTALLATION_TYPE_CHOICES = [
        ('wall', 'Devorga o\'rnatish'),
        ('ceiling', 'Shiftga o\'rnatish'),
        ('window_frame', 'Deraza romiga o\'rnatish'),
    ]
    
    # Buyurtma bilan bog'lanish
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Buyurtma'
    )
    
    # Jalyuzi tafsilotlari
    blind_type = models.CharField(
        max_length=30,
        choices=BLIND_TYPE_CHOICES,
        verbose_name='Jalyuzi turi'
    )
    width = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Eni (sm)'
    )
    height = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Bo\'yi (sm)'
    )
    material = models.CharField(
        max_length=20,
        choices=MATERIAL_CHOICES,
        verbose_name='Material turi'
    )
    installation_type = models.CharField(
        max_length=30,
        choices=INSTALLATION_TYPE_CHOICES,
        verbose_name='O\'rnatish turi'
    )
    mechanism_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Mexanizm turi'
    )
    cornice_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Karniz turi'
    )
    
    # Narx va miqdor
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Donasi'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Birlik narxi'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Umumiy narxi'
    )
    
    # Qo'shimcha ma'lumotlar
    room_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Xona nomi (masalan: Yotoq xona, Mehmonxona)'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    
    class Meta:
        verbose_name = 'Buyurtma elementi'
        verbose_name_plural = 'Buyurtma elementlari'
    
    def __str__(self):
        room = f" ({self.room_name})" if self.room_name else ""
        return f"{self.order.order_number} - {self.get_blind_type_display()}{room}"
    
    def save(self, *args, **kwargs):
        # Umumiy narxni hisoblash
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def area(self):
        """Maydon (m²)"""
        return (self.width * self.height) / 10000  # sm² dan m² ga
    
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