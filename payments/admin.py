# payments/admin.py - TUZATILGAN VERSIYA

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum
from .models import Payment, PaymentSchedule


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """To'lovlar admin paneli"""
    
    list_display = (
        'order_number', 'get_customer_name', 'payment_type', 'amount_display', 
        'payment_method', 'status_badge', 'payment_date', 'received_by'
    )
    list_filter = (
        'payment_type', 'payment_method', 'status', 
        'payment_date', 'received_by'
    )
    search_fields = (
        'order__order_number', 'order__customer__first_name', 
        'order__customer__last_name', 'reference_number'
    )
    readonly_fields = (
        'payment_date', 'confirmed_date', 'created_at', 'updated_at'
    )
    ordering = ('-payment_date',)
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('To\'lov ma\'lumotlari', {
            'fields': (
                'order', 'payment_type', 'amount', 'payment_method', 
                'reference_number', 'scheduled_date'
            )
        }),
        ('Status va tasdiqlash', {
            'fields': (
                'status', 'confirmed_by', 'confirmed_date'
            )
        }),
        ('Qaytarish ma\'lumotlari', {
            'fields': (
                'refund_reason', 'refunded_to_payment'
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
    
    def order_number(self, obj):
        """Buyurtma raqami"""
        return obj.order.order_number
    order_number.short_description = 'Buyurtma'
    order_number.admin_order_field = 'order__order_number'
    
    def get_customer_name(self, obj):
        """Mijoz ismi"""
        return obj.order.customer.full_name
    get_customer_name.short_description = 'Mijoz'
    get_customer_name.admin_order_field = 'order__customer__first_name'
    
    def amount_display(self, obj):
        """Summa ko'rsatish"""
        return f"{obj.amount:,.0f} so'm"
    amount_display.short_description = 'Summa'
    amount_display.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        """Status badge"""
        colors = {
            'pending': 'warning',
            'confirmed': 'success', 
            'cancelled': 'danger',
            'refunded': 'info'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['confirm_payments', 'cancel_payments']
    
    def confirm_payments(self, request, queryset):
        """Tanlangan to'lovlarni tasdiqlash"""
        confirmed_count = 0
        for payment in queryset.filter(status='pending'):
            payment.confirm_payment(request.user)
            confirmed_count += 1
        
        self.message_user(request, f'{confirmed_count} ta to\'lov tasdiqlandi.')
    confirm_payments.short_description = 'Tanlangan to\'lovlarni tasdiqlash'
    
    def cancel_payments(self, request, queryset):
        """Tanlangan to'lovlarni bekor qilish"""
        updated = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(request, f'{updated} ta to\'lov bekor qilindi.')
    cancel_payments.short_description = 'Tanlangan to\'lovlarni bekor qilish'


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    """To'lov rejasi admin paneli"""
    
    list_display = (
        'order_number', 'get_customer_name', 'installment_number', 
        'scheduled_amount_display', 'due_date', 'is_paid_badge', 'days_remaining'
    )
    list_filter = ('is_paid', 'due_date', 'created_at')
    search_fields = (
        'order__order_number', 'order__customer__first_name',
        'order__customer__last_name'
    )
    readonly_fields = ('created_at', 'days_remaining')
    ordering = ('due_date', 'installment_number')
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Buyurtma ma\'lumotlari', {
            'fields': ('order', 'installment_number')
        }),
        ('To\'lov rejasi', {
            'fields': (
                'scheduled_amount', 'due_date', 'is_paid', 'payment'
            )
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_number(self, obj):
        """Buyurtma raqami"""
        return obj.order.order_number
    order_number.short_description = 'Buyurtma'
    order_number.admin_order_field = 'order__order_number'
    
    def get_customer_name(self, obj):
        """Mijoz ismi"""
        return obj.order.customer.full_name
    get_customer_name.short_description = 'Mijoz'
    
    def scheduled_amount_display(self, obj):
        """Rejalashtirilgan summa"""
        return f"{obj.scheduled_amount:,.0f} so'm"
    scheduled_amount_display.short_description = 'Summa'
    scheduled_amount_display.admin_order_field = 'scheduled_amount'
    
    def is_paid_badge(self, obj):
        """To'langan badge"""
        if obj.is_paid:
            return format_html('<span class="badge bg-success">To\'langan</span>')
        elif obj.is_overdue:
            return format_html('<span class="badge bg-danger">Kechikkan</span>')
        else:
            return format_html('<span class="badge bg-warning">Kutilmoqda</span>')
    is_paid_badge.short_description = 'Holat'
    
    def days_remaining(self, obj):
        """Qolgan kunlar"""
        days = obj.days_until_due
        if obj.is_paid:
            return format_html('<span class="text-success">To\'langan</span>')
        elif days < 0:
            return format_html('<span class="text-danger">{} kun kechikdi</span>', abs(days))
        elif days == 0:
            return format_html('<span class="text-warning">Bugun</span>')
        else:
            return format_html('<span class="text-info">{} kun qoldi</span>', days)
    days_remaining.short_description = 'Muddati'
    
    actions = ['mark_as_paid', 'send_reminders']
    
    def mark_as_paid(self, request, queryset):
        """To'langan deb belgilash"""
        count = queryset.filter(is_paid=False).update(is_paid=True)
        self.message_user(request, f'{count} ta to\'lov to\'langan deb belgilandi.')
    mark_as_paid.short_description = 'To\'langan deb belgilash'
    
    def send_reminders(self, request, queryset):
        """Eslatma yuborish"""
        # Bu yerda SMS yoki email yuborish logikasi bo'ladi
        count = queryset.filter(is_paid=False).count()
        self.message_user(
            request, 
            f'{count} ta to\'lov uchun eslatma yuborish rejalashtirildi.'
        )
    send_reminders.short_description = 'Eslatma yuborish'


# Admin panel sarlavhalarini o'zgartirish
admin.site.site_header = "AYDIN AWLAD CRM - To'lovlar boshqaruvi"
admin.site.site_title = "AYDIN AWLAD CRM"
admin.site.index_title = "To'lovlar CRM tizimi"