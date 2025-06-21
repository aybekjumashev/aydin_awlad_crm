# accounts/models.py - TO'LIQ TUZATILGAN VERSIYA

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from decimal import Decimal


class User(AbstractUser):
    """
    Foydalanuvchi modeli - Property'lar bilan to'liq versiya
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Menejer'),
        ('technical', 'Texnik xodim'),
    ]
    
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
    
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Tug\'ilgan kun'
    )
    
    # Texnik xodim huquqlari
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
        verbose_name='Buyurtma bekor qilish',
        help_text='Buyurtmani bekor qilish huquqi'
    )
    can_manage_payments = models.BooleanField(
        default=False,
        verbose_name='To\'lovlarni boshqarish',
        help_text='To\'lov qabul qilish va boshqarish huquqi'
    )
    can_view_all_orders = models.BooleanField(
        default=False,
        verbose_name='Barcha buyurtmalarni ko\'rish',
        help_text='Texnik xodim barcha buyurtmalarni ko\'ra oladimi?'
    )
    
    # Ishchi ma'lumotlari
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
    
    # Vaqt ma'lumotlari
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
        """Saqlashdan oldin huquqlarni avtomatik belgilash"""
        
        # MUHIM: createsuperuser uchun maxsus logic
        if self.is_superuser and (not self.role or self.role == 'technical'):
            self.role = 'admin'
        
        # Rol bo'yicha huquqlarni avtomatik belgilash
        if self.role == 'admin':
            self.is_staff = True
            self.is_superuser = True
            self.can_create_order = True
            self.can_measure = True
            self.can_manufacture = True
            self.can_install = True
            self.can_cancel_order = True
            self.can_manage_payments = True
            self.can_view_all_orders = True
            
        elif self.role == 'manager':
            self.is_staff = True
            if not self.is_superuser:  
                self.is_superuser = False
            self.can_create_order = True
            self.can_measure = True
            self.can_manufacture = True
            self.can_install = True
            self.can_cancel_order = True
            self.can_manage_payments = True
            self.can_view_all_orders = True
            
        elif self.role == 'technical':
            if not self.is_superuser:
                self.is_staff = False
            self.can_view_all_orders = False
            
            # Mutaxassis turiga qarab huquqlar berish
            if self.specialist_type == 'universal':
                self.can_create_order = True
                self.can_measure = True
                self.can_manufacture = True
                self.can_install = True
                self.can_manage_payments = True
            elif self.specialist_type == 'measurer':
                self.can_create_order = True
                self.can_measure = True
                self.can_manage_payments = True
            elif self.specialist_type == 'manufacturer':
                self.can_manufacture = True
            elif self.specialist_type == 'installer':
                self.can_install = True
                self.can_manage_payments = True
        
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        """To'liq ismni qaytarish"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username
    
    def get_short_name(self):
        """Qisqa ismni qaytarish"""
        return self.first_name or self.username
    
    # MUHIM: Rol tekshirish property'lari
    @property
    def is_admin(self):
        """Admin ekanligini tekshirish"""
        return self.role == 'admin'
    
    @property
    def is_manager(self):
        """Menejer ekanligini tekshirish"""
        return self.role == 'manager'
    
    @property
    def is_technical(self):
        """Texnik xodim ekanligini tekshirish"""
        return self.role == 'technical'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"