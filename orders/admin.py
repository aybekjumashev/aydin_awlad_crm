# orders/admin.py

from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Buyurtma elementlari inline"""
    model = OrderItem
    extra = 0
    min_num = 0
    
    fields = (
        'blind_type', 'width', 'height', 'material', 'installation_type',
        'room_name', 'quantity', 'unit_price', 'total_price_display'
    )
    readonly_fields = ('total_price_display',)
    
    def total_price_display(self, obj):
        """Umumiy narx ko'rsatish"""
        if obj.pk:
            return f"{obj.total_price():,.0f} so'm"
        return "-"
    total_price_display.short_description = 'Umumiy narx'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Buyurtmalar admin"""
    
    list_display = (
        'order_number', 'customer_link', 'status_display', 'total_items_display',
        'total_price_display', 'payment_status_display', 'created_at', 'created_by'
    )
    list_filter = (
        'status', 'created_at', 'measurement_date', 'installation_date',
        'created_by', 'measured_by', 'processed_by', 'installed_by'
    )
    search_fields = (
        'order_number', 'customer__first_name', 'customer__last_name',
        'customer__phone', 'address', 'notes'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('customer', 'order_number', 'status', 'address')
        }),
        ('Jarayonlar', {
            'fields': (
                ('measured_by', 'measurement_date'),
                ('processed_by', 'processing_start_date'),
                ('installed_by', 'installation_date'),
            ),
            'classes': ('collapse',)
        }),
        ('Bekor qilish', {
            'fields': ('cancelled_by', 'cancelled_date', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
        ('Sanalar', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    def customer_link(self, obj):
        """Mijoz linkini ko'rsatish"""
        url = reverse('admin:customers_customer_change', args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.customer.get_full_name())
    customer_link.short_description = 'Mijoz'
    
    def status_display(self, obj):
        """Status ranglar bilan"""
        colors = {
            'new': '#6c757d',
            'measuring': '#ffc107',
            'processing': '#0dcaf0',
            'installed': '#198754',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Holat'
    
    def total_items_display(self, obj):
        """Jami elementlar soni"""
        return f"{obj.total_items()} ta"
    total_items_display.short_description = 'Elementlar'
    
    def total_price_display(self, obj):
        """Umumiy narx"""
        total = obj.total_price()
        if total > 0:
            return f"{total:,.0f} so'm"
        return "Narx kiritilmagan"
    total_price_display.short_description = 'Umumiy narx'
    
    def payment_status_display(self, obj):
        """To'lov holati"""
        status = obj.get_payment_status()
        colors = {
            'not_paid': '#dc3545',
            'partial': '#ffc107',
            'paid': '#198754',
        }
        color = colors.get(status['status'], '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status['label']
        )
    payment_status_display.short_description = 'To\'lov'
    
    def save_model(self, request, obj, form, change):
        """Saqlashda foydalanuvchini belgilash"""
        if not change:  # Yangi buyurtma
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """QuerySet optimizatsiyasi"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'created_by').prefetch_related('items', 'payments')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Buyurtma elementlari admin"""
    
    list_display = (
        'order_link', 'blind_type', 'dimensions_display', 'material',
        'quantity', 'unit_price', 'total_price_display', 'room_name'
    )
    list_filter = ('blind_type', 'material', 'installation_type', 'created_at')
    search_fields = (
        'order__order_number', 'order__customer__first_name',
        'order__customer__last_name', 'room_name', 'notes'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Buyurtma', {
            'fields': ('order',)
        }),
        ('Jalyuzi ma\'lumotlari', {
            'fields': (
                'blind_type', 'material', 'installation_type',
                ('width', 'height'), 'mechanism_type', 'cornice_type'
            )
        }),
        ('Miqdor va narx', {
            'fields': (('quantity', 'unit_price'), 'room_name')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        """Buyurtma linkini ko'rsatish"""
        url = reverse('admin:orders_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Buyurtma'
    
    def dimensions_display(self, obj):
        """O'lchamlar ko'rsatish"""
        return f"{obj.width} × {obj.height} sm"
    dimensions_display.short_description = 'O\'lchamlar'
    
    def total_price_display(self, obj):
        """Umumiy narx"""
        return f"{obj.total_price():,.0f} so'm"
    total_price_display.short_description = 'Umumiy narx'
    
    def get_queryset(self, request):
        """QuerySet optimizatsiyasi"""
        qs = super().get_queryset(request)
        return qs.select_related('order', 'order__customer')