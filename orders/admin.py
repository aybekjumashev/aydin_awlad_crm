
# orders/admin.py - Yangilangan

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    """Buyurtma elementlari inline - Yangilangan"""
    model = OrderItem
    extra = 0
    min_num = 1
    
    fields = (
        'blind_type', 'width', 'height', 'material', 'installation_type',
        'room_name', 'quantity', 'unit_price_per_sqm', 'unit_price_total',
        'area_display', 'total_price_display'
    )
    readonly_fields = ('area_display', 'total_price_display')
    
    def area_display(self, obj):
        """Maydon ko'rsatish"""
        if obj.pk:
            return f"{obj.total_area():.4f} m²"
        return "-"
    area_display.short_description = 'Umumiy maydon'
    
    def total_price_display(self, obj):
        """Umumiy narx ko'rsatish"""
        if obj.pk:
            return f"{obj.total_price():,.0f} so'm"
        return "-"
    total_price_display.short_description = 'Umumiy narx'


class OrderStatusHistoryInline(admin.TabularInline):
    """Holat tarixi inline"""
    model = OrderStatusHistory
    extra = 0
    
    fields = ('old_status', 'new_status', 'changed_by', 'notes', 'changed_at')
    readonly_fields = ('changed_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Buyurtmalar admin - Yangilangan versiya"""
    
    list_display = (
        'order_number', 'customer_link', 'status_badge', 'total_items_display',
        'total_area_display', 'total_price_display', 'payment_status_display',
        'location_link', 'created_at'
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
        ('GPS ma\'lumotlari', {
            'fields': ('latitude', 'longitude', 'location_accuracy'),
            'classes': ('collapse',)
        }),
        ('Jarayonlar', {
            'fields': (
                'measurement_date', 'measured_by', 'measurement_notes',
                'production_date', 'processed_by', 'production_notes',
                'installation_date', 'installed_by', 'installation_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Qo\'shimcha', {
            'fields': ('notes',)
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    actions = ['mark_as_measuring', 'mark_as_processing', 'mark_as_installed', 'export_orders']
    
    def customer_link(self, obj):
        """Mijoz havolasi"""
        url = reverse('admin:customers_customer_change', args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.customer.get_full_name())
    customer_link.short_description = 'Mijoz'
    
    def status_badge(self, obj):
        """Holat belgisi"""
        colors = {
            'new': 'primary',
            'measuring': 'warning',
            'processing': 'info',
            'installed': 'success',
            'cancelled': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Holat'
    
    def total_items_display(self, obj):
        """Jami elementlar"""
        return obj.total_items()
    total_items_display.short_description = 'Jami donalar'
    
    def total_area_display(self, obj):
        """Jami maydon"""
        area = obj.total_area()
        return f"{area:.4f} m²" if area else "0 m²"
    total_area_display.short_description = 'Jami maydon'
    
    def total_price_display(self, obj):
        """Jami narx"""
        price = obj.total_price()
        return f"{price:,.0f} so'm" if price else "0 so'm"
    total_price_display.short_description = 'Jami narx'
    
    def payment_status_display(self, obj):
        """To'lov holati"""
        total = obj.total_price()
        paid = obj.total_paid()
        
        if total == 0:
            return "Narx kiritilmagan"
        
        percentage = (paid / total) * 100 if total > 0 else 0
        
        if percentage >= 100:
            return format_html('<span style="color: green;">To\'langan</span>')
        elif percentage > 0:
            return format_html(
                '<span style="color: orange;">Qisman ({:.0f}%)</span>',
                percentage
            )
        else:
            return format_html('<span style="color: red;">To\'lanmagan</span>')
    payment_status_display.short_description = 'To\'lov'
    
    def location_link(self, obj):
        """Joylashuv havolasi"""
        if obj.latitude and obj.longitude:
            url = f"https://maps.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html(
                '<a href="{}" target="_blank"><i class="fas fa-map-marker-alt"></i></a>',
                url
            )
        return "-"
    location_link.short_description = 'GPS'
    
    def get_queryset(self, request):
        """QuerySet optimizatsiyasi"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'created_by').prefetch_related(
            'items', 'payments'
        )
    
    # Actions
    def mark_as_measuring(self, request, queryset):
        """O'lchovga belgilash"""
        updated = queryset.update(status='measuring')
        self.message_user(request, f'{updated} ta buyurtma o\'lchovga belgilandi.')
    mark_as_measuring.short_description = 'O\'lchovga belgilash'
    
    def mark_as_processing(self, request, queryset):
        """Ishlab chiqarishga belgilash"""
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} ta buyurtma ishlab chiqarishga belgilandi.')
    mark_as_processing.short_description = 'Ishlab chiqarishga belgilash'
    
    def mark_as_installed(self, request, queryset):
        """O'rnatildi deb belgilash"""
        updated = queryset.update(status='installed')
        self.message_user(request, f'{updated} ta buyurtma o\'rnatildi deb belgilandi.')
    mark_as_installed.short_description = 'O\'rnatildi deb belgilash'
    
    def export_orders(self, request, queryset):
        """Buyurtmalarni eksport qilish"""
        self.message_user(request, f'{queryset.count()} ta buyurtma eksport qilindi.')
    export_orders.short_description = 'Tanlangan buyurtmalarni eksport qilish'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Buyurtma elementlari admin"""
    
    list_display = (
        'order', 'blind_type', 'dimensions', 'material', 'room_name',
        'quantity', 'area_display', 'total_price_display'
    )
    list_filter = (
        'blind_type', 'material', 'installation_type', 'mechanism', 'created_at'
    )
    search_fields = (
        'order__order_number', 'order__customer__first_name',
        'order__customer__last_name', 'room_name', 'notes'
    )
    
    fieldsets = (
        ('Buyurtma', {
            'fields': ('order',)
        }),
        ('Jalyuzi ma\'lumotlari', {
            'fields': ('blind_type', 'material', 'width', 'height', 'quantity')
        }),
        ('O\'rnatish', {
            'fields': ('installation_type', 'mechanism', 'cornice_type')
        }),
        ('Narx', {
            'fields': ('unit_price_per_sqm', 'unit_price_total')
        }),
        ('Qo\'shimcha', {
            'fields': ('room_name', 'color', 'notes')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def dimensions(self, obj):
        """O'lchamlar"""
        return f"{obj.width}x{obj.height} sm"
    dimensions.short_description = 'O\'lcham'
    
    def area_display(self, obj):
        """Maydon"""
        return f"{obj.total_area():.4f} m²"
    area_display.short_description = 'Maydon'
    
    def total_price_display(self, obj):
        """Umumiy narx"""
        return f"{obj.total_price():,.0f} so'm"
    total_price_display.short_description = 'Umumiy narx'


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Buyurtma holati tarixi admin"""
    
    list_display = (
        'order', 'old_status', 'new_status', 'changed_by', 'changed_at'
    )
    list_filter = ('old_status', 'new_status', 'changed_at', 'changed_by')
    search_fields = (
        'order__order_number', 'order__customer__first_name',
        'order__customer__last_name', 'notes'
    )
    readonly_fields = ('changed_at',)
    
    fieldsets = (
        ('Buyurtma', {
            'fields': ('order',)
        }),
        ('Holat o\'zgarishi', {
            'fields': ('old_status', 'new_status', 'changed_by', 'changed_at')
        }),
        ('Izoh', {
            'fields': ('notes',)
        }),
    )


# Admin panel CSS qo'shimchalari
class AdminConfig:
    """Admin panel konfiguratsiyasi"""
    
    @staticmethod
    def get_admin_css():
        return """
        <style>
        .badge {
            display: inline-block;
            padding: 0.25em 0.4em;
            font-size: 75%;
            font-weight: 700;
            line-height: 1;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 0.25rem;
        }
        
        .badge-primary { background-color: #007bff; color: white; }
        .badge-warning { background-color: #ffc107; color: black; }
        .badge-info { background-color: #17a2b8; color: white; }
        .badge-success { background-color: #28a745; color: white; }
        .badge-danger { background-color: #dc3545; color: white; }
        .badge-secondary { background-color: #6c757d; color: white; }
        
        .admin-stats {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .admin-stats h3 {
            color: #495057;
            margin-bottom: 10px;
        }
        
        .stat-item {
            display: inline-block;
            margin-right: 20px;
            padding: 10px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }
        
        .stat-label {
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
        }
        </style>
        """


# Admin dasturida qo'shimcha sozlamalar
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum
from datetime import date, timedelta


class CustomAdminSite(AdminSite):
    """Maxsus admin paneli"""
    
    site_header = "AYDIN AWLAD CRM - Boshqaruv paneli"
    site_title = "AYDIN AWLAD CRM"
    index_title = "CRM tizimi boshqaruv paneli"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('stats/', self.admin_view(self.stats_view), name='stats'),
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def stats_view(self, request):
        """Statistika sahifasi"""
        from customers.models import Customer
        from orders.models import Order
        from payments.models import Payment
        
        today = date.today()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        # Asosiy statistikalar
        stats = {
            'total_customers': Customer.objects.count(),
            'total_orders': Order.objects.count(),
            'new_orders': Order.objects.filter(status='new').count(),
            'processing_orders': Order.objects.filter(status='processing').count(),
            'completed_orders': Order.objects.filter(status='installed').count(),
            
            # Bu oylik statistika
            'this_month_orders': Order.objects.filter(
                created_at__gte=this_month_start
            ).count(),
            'this_month_revenue': Payment.objects.filter(
                payment_date__gte=this_month_start,
                is_confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0,
            
            # O'tgan oylik
            'last_month_orders': Order.objects.filter(
                created_at__gte=last_month_start,
                created_at__lt=this_month_start
            ).count(),
            'last_month_revenue': Payment.objects.filter(
                payment_date__gte=last_month_start,
                payment_date__lt=this_month_start,
                is_confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        # Tug'ilgan kunlar (keyingi 7 kun)
        upcoming_birthdays = Customer.objects.filter(
            birth_date__isnull=False
        ).extra(
            select={
                'upcoming': """
                CASE 
                WHEN strftime('%m-%d', birth_date) >= strftime('%m-%d', 'now') 
                THEN strftime('%m-%d', birth_date)
                ELSE strftime('%m-%d', birth_date, '+1 year')
                END
                """
            }
        ).order_by('upcoming')[:10]
        
        # Eng faol mijozlar
        top_customers = Customer.objects.annotate(
            orders_count=Count('orders')
        ).filter(orders_count__gt=0).order_by('-orders_count')[:10]
        
        context = {
            'stats': stats,
            'upcoming_birthdays': upcoming_birthdays,
            'top_customers': top_customers,
            'title': 'Statistika',
        }
        
        return render(request, 'admin/stats.html', context)
    
    def dashboard_view(self, request):
        """Dashboard sahifasi"""
        return render(request, 'admin/dashboard.html', {
            'title': 'Dashboard'
        })


# Management command - ma'lumotlarni yangilash
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Ma'lumotlar bazasini yangilash buyrug'i"""
    
    help = 'AYDIN AWLAD CRM tizimini yangilash'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate',
            action='store_true',
            help='Migratsiyalarni ishga tushirish',
        )
        parser.add_argument(
            '--collectstatic',
            action='store_true',
            help='Statik fayllarni yig\'ish',
        )
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Superuser yaratish',
        )
    
    def handle(self, *args, **options):
        if options['migrate']:
            self.stdout.write('Migratsiyalar ishga tushirilmoqda...')
            from django.core.management import call_command
            call_command('makemigrations')
            call_command('migrate')
            self.stdout.write(
                self.style.SUCCESS('Migratsiyalar muvaffaqiyatli bajarildi!')
            )
        
        if options['collectstatic']:
            self.stdout.write('Statik fayllar yig\'ilmoqda...')
            from django.core.management import call_command
            call_command('collectstatic', '--noinput')
            self.stdout.write(
                self.style.SUCCESS('Statik fayllar muvaffaqiyatli yig\'ildi!')
            )
        
        if options['create_superuser']:
            self.stdout.write('Superuser yaratilmoqda...')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if not User.objects.filter(is_superuser=True).exists():
                User.objects.create_superuser(
                    username='admin',
                    email='admin@aydinawlad.uz',
                    password='admin123',
                    first_name='Admin',
                    last_name='User',
                    role='admin'
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        'Superuser yaratildi! '
                        'Username: admin, Password: admin123'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Superuser allaqachon mavjud!')
                )


# Fayllar ro'yxati yaratish uchun script
def create_file_structure():
    """Loyiha fayllar tuzilmasini yaratish"""
    
    import os
    
    # Asosiy papkalar
    directories = [
        'templates/customers',
        'templates/orders', 
        'templates/admin',
        'static/css',
        'static/js',
        'static/images',
        'media/uploads',
        'customers/management/commands',
        'orders/management/commands',
        'accounts/management/commands',
        'payments/management/commands',
        'reports/management/commands',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ {directory} papkasi yaratildi")
    
    # __init__.py fayllarini yaratish
    init_files = [
        'customers/management/__init__.py',
        'customers/management/commands/__init__.py',
        'orders/management/__init__.py', 
        'orders/management/commands/__init__.py',
        'accounts/management/__init__.py',
        'accounts/management/commands/__init__.py',
        'payments/management/__init__.py',
        'payments/management/commands/__init__.py',
        'reports/management/__init__.py',
        'reports/management/commands/__init__.py',
    ]
    
    for init_file in init_files:
        with open(init_file, 'w') as f:
            f.write('# Init file\n')
        print(f"✅ {init_file} yaratildi")
    
    print("\n🎉 Fayllar tuzilmasi muvaffaqiyatli yaratildi!")


if __name__ == '__main__':
    create_file_structure()