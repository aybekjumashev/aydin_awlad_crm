# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Foydalanuvchi modeli - 3 ta rol bilan
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Menejer'),
        ('technician', 'Texnik xodim'),
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='technician',
        verbose_name='Rol'
    )
    phone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name='Telefon raqam'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Qo\'shilgan sana'
    )
    
    # Texnik xodim uchun huquqlar
    can_create_order = models.BooleanField(
        default=False,
        verbose_name='Buyurtma yarata oladi'
    )
    can_measure = models.BooleanField(
        default=False,
        verbose_name='O\'lchash ishlari'
    )
    can_manufacture = models.BooleanField(
        default=False,
        verbose_name='Ishlab chiqarish'
    )
    can_install = models.BooleanField(
        default=False,
        verbose_name='O\'rnatish ishlari'
    )
    can_cancel_order = models.BooleanField(
        default=False,
        verbose_name='Buyurtmani bekor qila oladi'
    )
    
    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role == 'manager'
    
    def is_technician(self):
        return self.role == 'technician'