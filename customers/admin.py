# customers/admin.py - ODDIY VERSIYA

from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'phone', 'address_short', 'total_orders', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('first_name', 'last_name', 'phone', 'address')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'phone', 'address')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes',)
        }),
        ('Vaqt belgilari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        """To'liq ism"""
        return obj.get_full_name()
    get_full_name.short_description = 'To\'liq ism'
    get_full_name.admin_order_field = 'first_name'
    
    def address_short(self, obj):
        """Qisqartirilib manzil"""
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_short.short_description = 'Manzil'
    
    def total_orders(self, obj):
        """Buyurtmalar soni"""
        return obj.orders.count()
    total_orders.short_description = 'Buyurtmalar'