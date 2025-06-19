# payments/admin.py - TO'G'IRLANGAN VERSIYA

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Payment, PaymentPlan


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """To'lovlar admin paneli"""
    
    list_display = (
        'order', 'get_customer_name', 'payment_type', 'amount', 
        'payment_method', 'get_status_badge', 'payment_date', 'received_by'
    )
    list_filter = (
        'payment_type', 'payment_method', 'status', 'is_confirmed', 
        'payment_date', 'received_by'
    )
    search_fields = (
        'order__order_number', 'order__customer__first_name', 
        'order__customer__last_name', 'receipt_number'
    )
    readonly_fields = (
        'payment_date', 'confirmed_at', 'refunded_at', 'created_at', 'updated_at'
    )
    ordering = ('-payment_date',)
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('To\'lov ma\'lumotlari', {
            'fields': (
                'order', 'payment_type', 'amount', 'payment_method', 
                'receipt_number', 'scheduled_date'
            )
        }),
        ('Status va tasdiqlash', {
            'fields': (
                'status', 'is_confirmed', 'confirmed_by', 'confirmed_at'
            )
        }),
        ('Qaytarish ma\'lumotlari', {
            'fields': (
                'refund_reason', 'refunded_at', 'refunded_by'
            ),
            'classes': ('collapse',)
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'received_by')
        }),
        ('Vaqt belgilari', {
            'fields': ('payment_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_customer_name(self, obj):
        """Mijoz ismi"""
        return obj.order.customer.get_full_name()
    get_customer_name.short_description = 'Mijoz'
    get_customer_name.admin_order_field = 'order__customer__first_name'
    
    def get_status_badge(self, obj):
        """Status badge"""
        colors = {
            'pending': 'orange',
            'confirmed': 'green', 
            'cancelled': 'red',
            'refunded': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Saqlashda avtomatik maydonlarni to'ldirish"""
        if not obj.received_by:
            obj.received_by = request.user
        
        if obj.is_confirmed and not obj.confirmed_by:
            obj.confirmed_by = request.user
            obj.confirmed_at = timezone.now()
            obj.status = 'confirmed'
        
        super().save_model(request, obj, form, change)
    
    actions = ['confirm_payments', 'cancel_payments']
    
    def confirm_payments(self, request, queryset):
        """Tanlangan to'lovlarni tasdiqlash"""
        updated = 0
        for payment in queryset.filter(status='pending'):
            payment.is_confirmed = True
            payment.confirmed_by = request.user
            payment.confirmed_at = timezone.now()
            payment.status = 'confirmed'
            payment.save()
            updated += 1
        
        self.message_user(request, f'{updated} ta to\'lov tasdiqlandi.')
    confirm_payments.short_description = 'Tanlangan to\'lovlarni tasdiqlash'
    
    def cancel_payments(self, request, queryset):
        """Tanlangan to'lovlarni bekor qilish"""
        updated = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(request, f'{updated} ta to\'lov bekor qilindi.')
    cancel_payments.short_description = 'Tanlangan to\'lovlarni bekor qilish'


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    """To'lov rejasi admin paneli"""
    
    list_display = (
        'order', 'get_customer_name', 'total_amount', 'monthly_payment',
        'duration_months', 'get_remaining_amount', 'get_next_payment', 'is_active'
    )
    list_filter = ('is_active', 'duration_months', 'start_date', 'created_at')
    search_fields = (
        'order__order_number', 'order__customer__first_name',
        'order__customer__last_name'
    )
    readonly_fields = (
        'get_remaining_amount', 'get_next_payment', 'created_at'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Buyurtma ma\'lumotlari', {
            'fields': ('order', 'is_active')
        }),
        ('To\'lov rejasi', {
            'fields': (
                'total_amount', 'down_payment', 'monthly_payment',
                'duration_months', 'interest_rate', 'start_date'
            )
        }),
        ('Hisob-kitob', {
            'fields': ('get_remaining_amount', 'get_next_payment'),
            'classes': ('collapse',)
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_customer_name(self, obj):
        """Mijoz ismi"""
        return obj.order.customer.get_full_name()
    get_customer_name.short_description = 'Mijoz'
    
    def get_remaining_amount(self, obj):
        """Qolgan summa"""
        remaining = obj.remaining_amount()
        if remaining > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{:,.0f} so\'m</span>',
                remaining
            )
        return format_html('<span style="color: green;">To\'liq to\'landi</span>')
    get_remaining_amount.short_description = 'Qolgan summa'
    
    def get_next_payment(self, obj):
        """Keyingi to'lov sanasi"""
        next_date = obj.next_payment_date()
        if next_date:
            return format_html(
                '<span style="font-weight: bold;">{}</span>',
                next_date.strftime('%d.%m.%Y')
            )
        return format_html('<span style="color: green;">Tugallangan</span>')
    get_next_payment.short_description = 'Keyingi to\'lov'