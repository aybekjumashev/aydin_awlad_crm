# orders/admin.py

from django.contrib import admin
from .models import Order, OrderItem, OrderHistory
from payments.models import Payment

class OrderItemInline(admin.TabularInline):
    """Buyurtma ichida jalyuzilarni inline ko'rsatish"""
    model = OrderItem
    extra = 1
    fields = ('blind_type', 'width', 'height', 'material', 'quantity', 'unit_price', 'total_price', 'room_name')
    readonly_fields = ('total_price',)

class PaymentInline(admin.TabularInline):
    """Buyurtma ichida to'lovlarni inline ko'rsatish"""
    model = Payment
    extra = 0
    fields = ('payment_type', 'amount', 'payment_method', 'payment_date', 'received_by', 'is_confirmed')
    readonly_fields = ('payment_date',)

class OrderHistoryInline(admin.TabularInline):
    """Buyurtma ichida tarixni ko'rsatish"""
    model = OrderHistory
    extra = 0
    fields = ('action', 'old_status', 'new_status', 'performed_by', 'created_at', 'notes')
    readonly_fields = ('created_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'created_by', 'total_items', 'total_price', 'total_paid', 'remaining_balance', 'created_at')
    list_filter = ('status', 'created_at', 'created_by')  # Faqat mavjud maydonlar
    search_fields = ('order_number', 'customer__first_name', 'customer__last_name', 'customer__phone')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline, PaymentInline, OrderHistoryInline]
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('customer', 'order_number', 'status')
        }),
        ('Jarayon mas\'ullari', {
            'fields': ('measured_by', 'processed_by', 'installed_by', 'cancelled_by')
        }),
        ('Sanalar', {
            'fields': ('measurement_date', 'processing_start_date', 'installation_date', 'cancelled_date')
        }),
        ('Bekor qilish', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',)
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'created_by', 'updated_by')
        }),
        ('Vaqt belgilari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Yangi obyekt yaratilayotganda
            obj.created_by = request.user
        
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        
        # Yangi buyurtma uchun history yaratish
        if not change:
            obj.create_history(
                action='created',
                performed_by=request.user,
                notes='Buyurtma yaratildi'
            )

# OrderItem va OrderHistory ni alohida registered qilmaymiz
# Chunki ular Order ichida inline sifatida ko'rsatiladi
    
    def save_model(self, request, obj, form, change):
        if not change:  # Yangi obyekt yaratilayotganda
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'blind_type', 'width', 'height', 'material', 'quantity', 'total_price', 'room_name')
    list_filter = ('blind_type', 'material', 'installation_type')
    search_fields = ('order__order_number', 'order__customer__first_name', 'room_name')
    readonly_fields = ('total_price',)