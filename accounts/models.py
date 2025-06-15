# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Foydalanuvchi modeli - Admin, Menejer, Texnik xodim rollari
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
    
    # Texnik xodim huquqlari
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
    
    def get_full_name(self):
        """To'liq ism-familiya"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_admin(self):
        """Admin ekanligini tekshirish"""
        return self.role == 'admin' or self.is_superuser
    
    def is_manager(self):
        """Menejer ekanligini tekshirish"""
        return self.role == 'manager' or self.is_admin()
    
    def is_technician(self):
        """Texnik xodim ekanligini tekshirish"""
        return self.role == 'technician'
    
    def can_view_dashboard(self):
        """Dashboard ko'rish huquqi"""
        return True  # Barcha foydalanuvchilar ko'ra oladi
    
    def can_manage_customers(self):
        """Mijozlarni boshqarish huquqi"""
        return self.is_manager() or self.is_technician()
    
    def can_manage_orders(self):
        """Buyurtmalarni boshqarish huquqi"""
        return self.is_manager() or self.can_create_order
    
    def can_manage_payments(self):
        """To'lovlarni boshqarish huquqi"""
        return self.is_manager()
    
    def can_view_reports(self):
        """Hisobotlarni ko'rish huquqi"""
        return self.is_manager()
    
    def can_manage_staff(self):
        """Xodimlarni boshqarish huquqi"""
        return self.is_manager()
    
    def has_permission_for_order_action(self, action):
        """Buyurtma amaliyotlari uchun huquq tekshirish"""
        if self.is_manager():
            return True
            
        permission_map = {
            'measure': self.can_measure,
            'manufacture': self.can_manufacture,
            'install': self.can_install,
            'cancel': self.can_cancel_order,
            'create': self.can_create_order,
        }
        
        return permission_map.get(action, False)
    
    def get_dashboard_stats(self):
        """Foydalanuvchi uchun dashboard statistikasi"""
        from orders.models import Order
        from payments.models import Payment
        
        stats = {}
        
        if self.is_technician():
            # Texnik xodim statistikasi
            stats.update({
                'my_orders': Order.objects.filter(
                    models.Q(measured_by=self) |
                    models.Q(processed_by=self) |
                    models.Q(installed_by=self) |
                    models.Q(created_by=self)
                ).distinct().count(),
                'pending_measures': Order.objects.filter(
                    status='measuring', 
                    measured_by__isnull=True
                ).count() if self.can_measure else 0,
                'pending_installs': Order.objects.filter(
                    status='processing', 
                    installed_by__isnull=True
                ).count() if self.can_install else 0,
            })
        
        elif self.is_manager():
            # Menejer statistikasi
            from django.db.models import Sum
            stats.update({
                'created_orders': Order.objects.filter(created_by=self).count(),
                'received_payments': Payment.objects.filter(received_by=self).count(),
                'total_received': Payment.objects.filter(
                    received_by=self, 
                    is_confirmed=True
                ).aggregate(total=Sum('amount'))['total'] or 0,
            })
        
        return stats
    
    def save(self, *args, **kwargs):
        """Saqlashda avtomatik huquqlar berish"""
        # Admin va menejerlar uchun barcha huquqlar
        if self.role in ['admin', 'manager']:
            self.can_create_order = True
            self.can_measure = True
            self.can_manufacture = True
            self.can_install = True
            self.can_cancel_order = True
        
        super().save(*args, **kwargs)