# payments/admin.py

from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_type', 'amount', 'payment_method', 'payment_date', 'is_confirmed', 'received_by')
    list_filter = ('payment_type', 'payment_method', 'is_confirmed', 'payment_date')
    search_fields = ('order__order_number', 'order__customer__first_name', 'order__customer__last_name', 'receipt_number')
    readonly_fields = ('payment_date', 'confirmed_at')
    
    fieldsets = (
        ('To\'lov ma\'lumotlari', {
            'fields': ('order', 'payment_type', 'amount', 'payment_method', 'payment_date')
        }),
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('receipt_number', 'notes', 'received_by')
        }),
        ('Tasdiqlash', {
            'fields': ('is_confirmed', 'confirmed_by', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.received_by:
            obj.received_by = request.user
        if obj.is_confirmed and not obj.confirmed_by:
            obj.confirmed_by = request.user
        super().save_model(request, obj, form, change)