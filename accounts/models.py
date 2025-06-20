# accounts/models.py - YANGILANGAN VERSIYA

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Foydalanuvchi modeli - Yangilangan versiya
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Menejer'),
        ('technical', 'Texnik xodim'),
    ]
    
    # YANGI: Texnik xodim turlari
    SPECIALIST_TYPE_CHOICES = [
        ('measurer', 'O\'lchov oluvchi'),
        ('manufacturer', 'Ishlab chiquvchi'),
        ('installer', 'O\'rnatuvchi'),
        ('universal', 'Universal (barchasi)'),
    ]
    
    # Asosiy ma'lumotlar
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='technical',
        verbose_name='Rol'
    )
    
    # YANGI: Texnik xodim turi
    specialist_type = models.CharField(
        max_length=20,
        choices=SPECIALIST_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='Mutaxassis turi',
        help_text='Faqat texnik xodimlar uchun'
    )
    
    # Kontakt ma'lumotlari
    phone_regex = RegexValidator(
        regex=r'^\+?998\d{9}$',
        message="Telefon raqam formati: +998901234567"
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=13,
        blank=True,
        null=True,
        verbose_name='Telefon raqam'
    )
    
    # Tug'ilgan kun (yangi)
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Tug\'ilgan kun'
    )
    
    # YANGILANGAN: Texnik xodim huquqlari
    can_create_order = models.BooleanField(
        default=False,
        verbose_name='Buyurtma yaratish',
        help_text='Yangi buyurtma qabul qilish huquqi'
    )
    can_measure = models.BooleanField(
        default=False,
        verbose_name='O\'lchov olish',
        help_text='Mijoz uyiga borib o\'lchov olish huquqi'
    )
    can_manufacture = models.BooleanField(
        default=False,
        verbose_name='Ishlab chiqarish',
        help_text='Jalyuzilarni ishlab chiqarish huquqi'
    )
    can_install = models.BooleanField(
        default=False,
        verbose_name='O\'rnatish',
        help_text='Jalyuzilarni o\'rnatish huquqi'
    )
    can_cancel_order = models.BooleanField(
        default=False,
        verbose_name='Buyurtmani bekor qilish',
        help_text='Buyurtmani bekor qilish huquqi'
    )
    
    # YANGI: To'lov bilan ishlash huquqi
    can_manage_payments = models.BooleanField(
        default=False,
        verbose_name='To\'lovlarni boshqarish',
        help_text='To\'lov qabul qilish va boshqarish huquqi'
    )
    
    # Ish ma'lumotlari (yangi)
    hire_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Ishga qabul qilingan sana'
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Maosh',
        help_text='Oylik maosh so\'mda'
    )
    
    # Qo'shimcha ma'lumotlar
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='Manzil'
    )
    emergency_contact = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Favqulodda holat uchun aloqa'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izohlar'
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
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Vaqtincha avtomatik permission logic ni o'chirish
        super().save(*args, **kwargs)
    
    def set_role_permissions(self):
        """Rolga qarab huquqlarni avtomatik belgilash"""
        if self.role == 'admin':
            # Admin barcha huquqlarga ega
            self.is_staff = True
            self.is_superuser = True
            self.can_create_order = True
            self.can_measure = True
            self.can_manufacture = True
            self.can_install = True
            self.can_cancel_order = True
            self.can_manage_payments = True
            
        elif self.role == 'manager':
            # Menejer ko'p huquqlarga ega, lekin superuser emas
            self.is_staff = True
            self.is_superuser = False
            self.can_create_order = True
            self.can_measure = True
            self.can_manufacture = True
            self.can_install = True
            self.can_cancel_order = True
            self.can_manage_payments = True
            
        elif self.role == 'technical':
            # Texnik xodim - faqat belgilangan huquqlar
            self.is_staff = False
            self.is_superuser = False
            
            # Mutaxassis turiga qarab huquqlar berish
            if self.specialist_type == 'universal':
                # Universal xodim barcha texnik ishlarni qila oladi
                self.can_create_order = True
                self.can_measure = True
                self.can_manufacture = True
                self.can_install = True
                self.can_cancel_order = False  # Faqat menejer yoki admin
                self.can_manage_payments = False  # Faqat menejer yoki admin
                
            elif self.specialist_type == 'measurer':
                # Faqat o'lchov olish
                self.can_create_order = True
                self.can_measure = True
                self.can_manufacture = False
                self.can_install = False
                self.can_cancel_order = False
                self.can_manage_payments = False
                
            elif self.specialist_type == 'manufacturer':
                # Faqat ishlab chiqarish
                self.can_create_order = False
                self.can_measure = False
                self.can_manufacture = True
                self.can_install = False
                self.can_cancel_order = False
                self.can_manage_payments = False
                
            elif self.specialist_type == 'installer':
                # Faqat o'rnatish
                self.can_create_order = False
                self.can_measure = False
                self.can_manufacture = False
                self.can_install = True
                self.can_cancel_order = False
                self.can_manage_payments = False
    
    # Properties for templates
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_technical(self):
        return self.role == 'technical'
    
    @property
    def can_manage_staff(self):
        """Xodimlarni boshqarish huquqi"""
        return self.role in ['admin', 'manager']
    
    @property
    def can_view_all_orders(self):
        """Barcha buyurtmalarni ko'rish huquqi"""
        return self.role in ['admin', 'manager']
    
    @property
    def can_edit_order_details(self):
        """Buyurtma tafsilotlarini tahrirlash huquqi"""
        return self.role in ['admin', 'manager']
    
    @property
    def can_manage_customers(self):
        """Mijozlarni boshqarish huquqi"""
        return self.role in ['admin', 'manager']
    
    @property
    def can_view_reports(self):
        """Hisobotlarni ko'rish huquqi"""
        return self.role in ['admin', 'manager']
    
    def get_full_name(self):
        """To'liq ism qaytarish"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_assigned_orders_count(self):
        """Tayinlangan buyurtmalar soni"""
        if not self.is_technical:
            return 0
            
        count = 0
        if self.can_measure:
            count += self.assigned_measurements.exclude(status__in=['installed', 'cancelled']).count()
        if self.can_manufacture:
            count += self.assigned_manufacturing.exclude(status__in=['installed', 'cancelled']).count()
        if self.can_install:
            count += self.assigned_installations.exclude(status__in=['installed', 'cancelled']).count()
        
        return count
    
    def has_perm(self, perm, obj=None):
        """Django admin uchun huquqlarni tekshirish"""
        if self.is_active and self.is_superuser:
            return True
        return False
    
    def has_module_perms(self, app_label):
        """Django admin uchun app huquqlarini tekshirish"""
        if self.is_active and self.is_staff:
            return True
        return False
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"