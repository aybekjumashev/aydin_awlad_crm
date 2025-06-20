# orders/admin.py - TUZATILGAN VERSIYA

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Buyurtma elementlari inline"""
    model = OrderItem
    extra = 0
    min_num = 0
    
    fields = (
        'blind_type', 'width', 'height', 'material', 'installation_type',
        'room_name', 'quantity', 'unit_price_per_sqm', 'unit_price_total',
        'area_display', 'total_price_display'
    )
    readonly_fields = ('area_display', 'total_price_display')
    
    def area_display(self, obj):
        """Maydon ko'rsatish"""
        if obj.pk:
            return f"{obj.area:.4f} m²"
        return "-"
    area_display.short_description = 'Maydon'
    
    def total_price_display(self, obj):
        """Umumiy narx ko'rsatish"""
        if obj.pk:
            return f"{obj.total_price:,.0f} so'm"
        return "-"
    total_price_display.short_description = 'Umumiy narx'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Buyurtmalar admin"""
    
    list_display = (
        'order_number', 'customer_link', 'status_badge', 'total_items_display',
        'total_amount', 'payment_status_display', 'created_at'
    )
    list_filter = (
        'status', 'payment_status', 'created_at', 'measurement_date', 'installation_date'
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
        ('To\'lov ma\'lumotlari', {
            'fields': ('total_amount', 'paid_amount', 'payment_status'),
            'classes': ('collapse',)
        }),
        ('Xodimlar tayinlanishi', {
            'fields': ('assigned_measurer', 'assigned_manufacturer', 'assigned_installer'),
            'classes': ('collapse',)
        }),
        ('Sanalar', {
            'fields': (
                'measurement_date', 'measurement_completed_date',
                'production_start_date', 'production_completed_date',
                'installation_date', 'installation_completed_date'
            ),
            'classes': ('collapse',)
        }),
        ('Izohlar', {
            'fields': ('notes', 'measurement_notes', 'production_notes', 'installation_notes'),
            'classes': ('collapse',)
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    inlines = [OrderItemInline]
    
    def customer_link(self, obj):
        """Mijoz havolasi"""
        url = reverse('admin:customers_customer_change', args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.customer.full_name)
    customer_link.short_description = 'Mijoz'
    
    def status_badge(self, obj):
        """Status badge"""
        colors = {
            'new': 'primary',
            'measuring': 'info', 
            'processing': 'warning',
            'installing': 'secondary',
            'installed': 'success',
            'cancelled': 'danger'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Holat'
    
    def total_items_display(self, obj):
        """Jalyuzilar soni"""
        count = obj.items.count()
        return f"{count} ta"
    total_items_display.short_description = 'Jalyuzilar'
    
    def payment_status_display(self, obj):
        """To'lov holati"""
        colors = {
            'pending': 'danger',
            'partial': 'warning', 
            'paid': 'success',
            'overpaid': 'info'
        }
        color = colors.get(obj.payment_status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_display.short_description = 'To\'lov'
    
    actions = ['mark_as_measuring', 'mark_as_processing', 'mark_as_installed']
    
    def mark_as_measuring(self, request, queryset):
        """O'lchovga yuborish"""
        updated = queryset.update(status='measuring')
        self.message_user(request, f'{updated} ta buyurtma o\'lchovga yuborildi.')
    mark_as_measuring.short_description = 'O\'lchovga yuborish'
    
    def mark_as_processing(self, request, queryset):
        """Ishlab chiqarishga yuborish"""
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} ta buyurtma ishlab chiqarishga yuborildi.')
    mark_as_processing.short_description = 'Ishlab chiqarishga yuborish'
    
    def mark_as_installed(self, request, queryset):
        """O'rnatildi deb belgilash"""
        updated = queryset.update(status='installed')
        self.message_user(request, f'{updated} ta buyurtma o\'rnatildi deb belgilandi.')
    mark_as_installed.short_description = 'O\'rnatildi deb belgilash'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Buyurtma elementlari admin"""
    
    list_display = (
        'order_number', 'blind_type_display', 'dimensions', 'material',
        'room_name', 'quantity', 'total_price_display'
    )
    list_filter = ('blind_type', 'material', 'installation_type', 'mechanism')
    search_fields = ('order__order_number', 'room_name', 'color')
    ordering = ('order__created_at',)
    
    def order_number(self, obj):
        """Buyurtma raqami"""
        return obj.order.order_number
    order_number.short_description = 'Buyurtma'
    
    def blind_type_display(self, obj):
        """Jalyuzi turi"""
        return obj.get_blind_type_display()
    blind_type_display.short_description = 'Turi'
    
    def dimensions(self, obj):
        """O'lchamlar"""
        return f"{obj.width} × {obj.height} sm"
    dimensions.short_description = 'O\'lcham'
    
    def total_price_display(self, obj):
        """Umumiy narx"""
        return f"{obj.total_price:,.0f} so'm"
    total_price_display.short_description = 'Narx'


# Admin panel sarlavhalarini o'zgartirish
admin.site.site_header = "AYDIN AWLAD CRM - Boshqaruv paneli"
admin.site.site_title = "AYDIN AWLAD CRM"
admin.site.index_title = "CRM tizimi boshqaruv paneli"