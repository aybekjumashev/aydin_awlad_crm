# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Foydalanuvchi yaratish formasi"""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class CustomUserChangeForm(UserChangeForm):
    """Foydalanuvchi tahrirlash formasi"""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 
                 'is_active', 'is_staff', 'can_create_order', 'can_measure', 
                 'can_manufacture', 'can_install', 'can_cancel_order')


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Foydalanuvchilar uchun admin sozlamalari"""
    
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = (
        'username', 'get_full_name', 'email', 'role', 'phone', 
        'is_active', 'is_staff', 'created_at'
    )
    list_filter = (
        'role', 'is_active', 'is_staff', 'created_at',
        'can_create_order', 'can_measure', 'can_manufacture', 'can_install'
    )
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Rol va huquqlar', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Texnik xodim huquqlari', {
            'fields': ('can_create_order', 'can_measure', 'can_manufacture', 
                      'can_install', 'can_cancel_order'),
            'classes': ('collapse',),
            'description': 'Texnik xodimlar uchun maxsus huquqlar'
        }),
        ('Sanalar', {
            'fields': ('last_login', 'date_joined', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 
                      'role', 'phone', 'password1', 'password2'),
        }),
        ('Texnik xodim huquqlari', {
            'classes': ('collapse',),
            'fields': ('can_create_order', 'can_measure', 'can_manufacture', 
                      'can_install', 'can_cancel_order'),
        }),
    )
    
    readonly_fields = ('created_at', 'last_login', 'date_joined')
    
    def get_full_name(self, obj):
        """To'liq ism ko'rsatish"""
        return obj.get_full_name()
    get_full_name.short_description = 'To\'liq ism'
    
    def save_model(self, request, obj, form, change):
        """Saqlashda avtomatik sozlamalar"""
        if not change:  # Yangi foydalanuvchi
            if obj.role in ['admin', 'manager']:
                obj.is_staff = True
                # Admin va menejerlar uchun barcha huquqlar
                obj.can_create_order = True
                obj.can_measure = True
                obj.can_manufacture = True
                obj.can_install = True
                obj.can_cancel_order = True
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """QuerySet optimizatsiyasi"""
        qs = super().get_queryset(request)
        return qs.select_related()


# Admin panel sarlavhalarini o'zgartirish
admin.site.site_header = "AYDIN AWLAD CRM - Boshqaruv paneli"
admin.site.site_title = "AYDIN AWLAD CRM"
admin.site.index_title = "CRM tizimi boshqaruv paneli"