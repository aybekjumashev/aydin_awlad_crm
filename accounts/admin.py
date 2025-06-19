# accounts/admin.py - ODDIY VERSIYA

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Foydalanuvchilar uchun admin sozlamalari"""
    
    list_display = (
        'username', 'get_full_name', 'email', 'role', 'phone', 
        'is_active', 'is_staff', 'created_at'
    )
    list_filter = ('role', 'is_active', 'is_staff', 'created_at')
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
    )
    
    readonly_fields = ('created_at', 'date_joined')
    
    def get_full_name(self, obj):
        """To'liq ism ko'rsatish"""
        return obj.get_full_name()
    get_full_name.short_description = 'To\'liq ism'


# Admin panel sarlavhalarini o'zgartirish
admin.site.site_header = "AYDIN AWLAD CRM - Boshqaruv paneli"
admin.site.site_title = "AYDIN AWLAD CRM"
admin.site.index_title = "CRM tizimi boshqaruv paneli"