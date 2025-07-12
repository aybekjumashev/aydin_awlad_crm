# customers/admin.py - TO'G'IRLANGAN VERSIYA

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Customer, CustomerPhone, CustomerNote


class CustomerPhoneInline(admin.TabularInline):
    """Mijoz telefon raqamlari inline"""
    model = CustomerPhone
    extra = 1
    max_num = 5


class CustomerNoteInline(admin.StackedInline):
    """Mijoz eslatmalari inline"""
    model = CustomerNote
    extra = 0
    readonly_fields = ('created_by', 'created_at')
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Mijozlar admin paneli"""
    
    list_display = (
        'get_full_name', 'phone', 'category', 'get_age_display', 
        'total_orders', 'get_debt_status', 'created_at'
    )
    list_filter = (
        'category', 'created_at', 'birth_date', 'created_by'
    )
    search_fields = (
        'first_name', 'last_name', 'phone', 'address'
    )
    readonly_fields = (
        'public_uuid', 'created_at', 'updated_at', 'get_public_link',
        'get_age_display', 'total_orders', 'total_paid_amount', 'total_debt'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'birth_date', 'category')
        }),
        ('Aloqa ma\'lumotlari', {
            'fields': ('phone', 'address')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('public_uuid', 'get_public_link', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Statistika', {
            'fields': ('get_age_display', 'total_orders', 'total_paid_amount', 'total_debt'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CustomerPhoneInline, CustomerNoteInline]
    
    def get_full_name(self, obj):
        """To'liq ism ko'rsatish"""
        return obj.get_full_name()
    get_full_name.short_description = 'To\'liq ism'
    get_full_name.admin_order_field = 'first_name'
    
    def get_age_display(self, obj):
        """Yosh ko'rsatish"""
        age = obj.get_age()
        if age:
            return f"{age} yosh"
        return "-"
    get_age_display.short_description = 'Yoshi'
    
    def get_debt_status(self, obj):
        """Qarzdorlik holati"""
        debt = obj.total_debt()
        if debt > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} so\'m</span>',
                debt
            )
        return format_html('<span style="color: green;">✓ To\'liq</span>')
    get_debt_status.short_description = 'Qarzdorlik'
    

    def get_public_link(self, obj):
        """Public sahifa havolasi"""
        if obj.pk:
            url = obj.get_public_url()
            return format_html(
                '<a href="{}" target="_blank">Mijoz sahifasi</a>',
                url
            )
        return "-"
    get_public_link.short_description = 'Public sahifa'
    
    def save_model(self, request, obj, form, change):
        """Saqlashda created_by ni o'rnatish"""
        if not change:  # Yangi obyekt
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_vip', 'mark_as_regular', 'mark_as_inactive']
    
    def mark_as_vip(self, request, queryset):
        """VIP qilib belgilash"""
        updated = queryset.update(category='vip')
        self.message_user(request, f'{updated} ta mijoz VIP qilib belgilandi.')
    mark_as_vip.short_description = 'Tanlangan mijozlarni VIP qilish'
    
    def mark_as_regular(self, request, queryset):
        """Oddiy qilib belgilash"""
        updated = queryset.update(category='regular')
        self.message_user(request, f'{updated} ta mijoz oddiy qilib belgilandi.')
    mark_as_regular.short_description = 'Tanlangan mijozlarni oddiy qilish'
    
    def mark_as_inactive(self, request, queryset):
        """Nofaol qilib belgilash"""
        updated = queryset.update(category='inactive')
        self.message_user(request, f'{updated} ta mijoz nofaol qilib belgilandi.')
    mark_as_inactive.short_description = 'Tanlangan mijozlarni nofaol qilish'


@admin.register(CustomerPhone)
class CustomerPhoneAdmin(admin.ModelAdmin):
    """Mijoz telefon raqamlari admin"""
    
    list_display = ('customer', 'phone_number', 'phone_type', 'is_primary', 'created_at')
    list_filter = ('phone_type', 'is_primary', 'created_at')
    search_fields = ('customer__first_name', 'customer__last_name', 'phone_number')
    ordering = ('-created_at',)


@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    """Mijoz eslatmalari admin"""
    
    list_display = ('customer', 'get_note_preview', 'is_important', 'created_by', 'created_at')
    list_filter = ('is_important', 'created_by', 'created_at')
    search_fields = ('customer__first_name', 'customer__last_name', 'note')
    readonly_fields = ('created_by', 'created_at')
    ordering = ('-created_at',)
    
    def get_note_preview(self, obj):
        """Eslatma preview"""
        return obj.note[:100] + "..." if len(obj.note) > 100 else obj.note
    get_note_preview.short_description = 'Eslatma'
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)