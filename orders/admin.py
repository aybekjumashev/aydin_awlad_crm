# orders/admin.py - GPS FIELDLAR BILAN YANGILANGAN

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['blind_type', 'width', 'height', 'material', 'quantity', 'unit_price']
    readonly_fields = ['total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 
        'customer_name', 
        'status', 
        'total_amount', 
        'payment_status',
        'has_gps_display',
        'created_at'
    ]
    
    list_filter = [
        'status', 
        'payment_status', 
        'created_at',
        'measurement_completed_date',
        'production_completed_date',
        'installation_completed_date'
    ]
    
    search_fields = [
        'order_number',
        'customer__first_name',
        'customer__last_name', 
        'customer__phone',
        'address'
    ]
    
    readonly_fields = [
        'order_number',
        'remaining_amount',
        'progress_percentage',
        'gps_location_display',
        'maps_links'
    ]
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('order_number', 'customer', 'status', 'address')
        }),
        ('GPS Joylashuv', {
            'fields': (
                'measurement_latitude', 
                'measurement_longitude', 
                'measurement_location_accuracy',
                'gps_location_display',
                'maps_links'
            ),
            'classes': ('collapse',),
            'description': 'O\'lchov vaqtida belgilangan GPS koordinatalar'
        }),
        ('Narx va To\'lov', {
            'fields': ('total_amount', 'paid_amount', 'payment_status', 'remaining_amount')
        }),
        ('Texnik xodimlar', {
            'fields': ('assigned_measurer', 'assigned_manufacturer', 'assigned_installer'),
            'classes': ('collapse',)
        }),
        ('Jarayon sanalari', {
            'fields': (
                'measurement_date',
                'measurement_completed_date', 
                'production_start_date',
                'production_completed_date',
                'installation_completed_date'
            ),
            'classes': ('collapse',)
        }),
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('notes', 'measurement_notes'),
            'classes': ('collapse',)
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at', 'updated_at', 'progress_percentage'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [OrderItemInline]
    
    def customer_name(self, obj):
        return obj.customer.get_full_name()
    customer_name.short_description = 'Mijoz'
    
    def has_gps_display(self, obj):
        if obj.has_gps_location:
            return format_html(
                '<span style="color: green;">✓ GPS mavjud</span>'
            )
        return format_html(
            '<span style="color: red;">✗ GPS yo\'q</span>'
        )
    has_gps_display.short_description = 'GPS Holati'
    
    def gps_location_display(self, obj):
        if obj.has_gps_location:
            return format_html(
                '<div style="font-family: monospace;">'
                '<strong>Kenglik:</strong> {}<br>'
                '<strong>Uzunlik:</strong> {}<br>'
                '<strong>Aniqlik:</strong> {}'
                '</div>',
                obj.measurement_latitude,
                obj.measurement_longitude,
                obj.measurement_location_accuracy or 'Noma\'lum'
            )
        return "GPS ma'lumot yo'q"
    gps_location_display.short_description = 'GPS Koordinatalar'
    
    def maps_links(self, obj):
        if obj.has_gps_location:
            google_url = obj.google_maps_url
            yandex_url = obj.yandex_maps_url
            
            return format_html(
                '<div>'
                '<a href="{}" target="_blank" class="button" style="margin-right: 10px;">'
                '📍 Google Maps</a>'
                '<a href="{}" target="_blank" class="button">'
                '🗺️ Yandex Maps</a>'
                '</div>',
                google_url,
                yandex_url
            )
        return "GPS ma'lumot yo'q"
    maps_links.short_description = 'Xarita havolalari'
    
    def remaining_amount(self, obj):
        amount = obj.remaining_amount
        if amount > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} so\'m</span>',
                amount
            )
        return format_html(
            '<span style="color: green;">✓ To\'liq to\'langan</span>'
        )
    remaining_amount.short_description = 'Qolgan summa'
    
    def progress_percentage(self, obj):
        percentage = obj.progress_percentage
        color = 'red' if percentage < 50 else 'orange' if percentage < 100 else 'green'
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px; '
            'text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            percentage, color, percentage
        )
    progress_percentage.short_description = 'Jarayon %'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order_number',
        'blind_type',
        'dimensions',
        'material',
        'quantity',
        'unit_price',
        'total_price',
        'created_at'
    ]
    
    list_filter = [
        'blind_type',
        'material',
        'installation_type',
        'mechanism',
        'created_at'
    ]
    
    search_fields = [
        'order__order_number',
        'order__customer__first_name',
        'order__customer__last_name',
        'blind_type',
        'material'
    ]
    
    readonly_fields = ['total_price', 'area']
    
    fieldsets = (
        ('Buyurtma ma\'lumotlari', {
            'fields': ('order',)
        }),
        ('Jalyuzi ma\'lumotlari', {
            'fields': ('blind_type', 'width', 'height', 'material', 'room_name')
        }),
        ('Texnik ma\'lumotlar', {
            'fields': ('installation_type', 'mechanism', 'cornice_type'),
            'classes': ('collapse',)
        }),
        ('Narx ma\'lumotlari', {
            'fields': ('quantity', 'unit_price', 'total_price', 'area')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )
    
    def order_number(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.order.order_number
        )
    order_number.short_description = 'Buyurtma'
    
    def dimensions(self, obj):
        return f"{obj.width} x {obj.height} sm"
    dimensions.short_description = 'O\'lcham'
    
    def total_price(self, obj):
        return f"{obj.total_price:,.0f} so'm"
    total_price.short_description = 'Umumiy narx'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__customer')

# Admin panelda GPS ma'lumotlarni yanada chiroyli ko'rsatish uchun CSS
admin.site.index_template = 'admin/custom_index.html'  # Agar custom template kerak bo'lsa

# Admin panel uchun qo'shimcha CSS va JavaScript
class AdminGPSMedia:
    css = {
        'all': ('admin/css/gps_admin.css',)
    }
    js = ('admin/js/gps_admin.js',)