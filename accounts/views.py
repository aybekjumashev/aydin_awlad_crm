# accounts/views.py - TUZATILGAN VERSIYA

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, timedelta

# Import models
from .models import User
from orders.models import Order
from customers.models import Customer
from payments.models import Payment
from .technical_views import my_tasks

@login_required
def dashboard(request):
    """Asosiy dashboard sahifasi - foydalanuvchi turiga qarab"""
    
    # Texnik xodim uchun maxsus dashboard
    if request.user.is_technical:
        return my_tasks(request)
    
    # Admin va menejer uchun umumiy dashboard
    return manager_dashboard(request)



def technical_dashboard(request):
    """Texnik xodim uchun dashboard - TUZATILGAN VERSIYA"""
    
    user = request.user
    today = date.today()
    
    # ✅ TUZATILDI: To'g'ri field nomlarini ishlatish
    my_orders = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user)
    ).exclude(status__in=['installed', 'cancelled']).select_related('customer')
    
    # Bugungi vazifalar
    today_tasks = []
    
    # O'lchov vazifalari
    if user.can_measure:
        measuring_today = my_orders.filter(
            assigned_measurer=user,
            status='measuring'
        )
        for order in measuring_today:
            today_tasks.append({
                'order': order,
                'task_type': 'measure',
                'task_name': 'O\'lchov olish',
                'icon': 'bi-rulers',
                'color': 'info',
                'url': f'/orders/{order.pk}/measurement/'
            })
    
    # Ishlab chiqarish vazifalari
    if user.can_manufacture:
        manufacturing_today = my_orders.filter(
            assigned_manufacturer=user,
            status='processing'
        )
        for order in manufacturing_today:
            today_tasks.append({
                'order': order,
                'task_type': 'manufacture',
                'task_name': 'Ishlab chiqarish',
                'icon': 'bi-tools',
                'color': 'warning',
                'url': f'/orders/{order.pk}/manufacturing/'
            })
    
    # O'rnatish vazifalari
    if user.can_install:
        installation_today = my_orders.filter(
            assigned_installer=user,
            status='installing'
        )
        for order in installation_today:
            today_tasks.append({
                'order': order,
                'task_type': 'install',
                'task_name': 'O\'rnatish',
                'icon': 'bi-house-gear',
                'color': 'success',
                'url': f'/orders/{order.pk}/installation/'
            })
    
    # Statistika
    stats = {
        'total_assigned': my_orders.count(),
        'measuring': my_orders.filter(status='measuring').count(),
        'processing': my_orders.filter(status='processing').count(),
        'installing': my_orders.filter(status='installing').count(),
        'today_tasks': len(today_tasks),
    }
    
    context = {
        'today_tasks': today_tasks,
        'my_orders': my_orders[:10],  # Oxirgi 10 ta
        'stats': stats,
        'user': user,
        'title': 'Texnik xodim paneli'
    }
    
    return render(request, 'accounts/technical_dashboard.html', context)


def manager_dashboard(request):
    """Admin va menejer uchun dashboard"""
    
    # So'nggi buyurtmalar
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
    
    # Statistikalar
    stats = {
        'total_orders': Order.objects.count(),
        'measuring_orders': Order.objects.filter(status='measuring').count(),
        'processing_orders': Order.objects.filter(status='processing').count(),
        'installing_orders': Order.objects.filter(status='installing').count(),
        'completed_orders': Order.objects.filter(status='installed').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
        'total_customers': Customer.objects.count(),
        'total_revenue': Payment.objects.filter(
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # Bu oyning statistikasi
    current_month = timezone.now().replace(day=1)
    month_stats = {
        'orders': Order.objects.filter(created_at__gte=current_month).count(),
        'revenue': Payment.objects.filter(
            created_at__gte=current_month,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'customers': Customer.objects.filter(created_at__gte=current_month).count(),
    }
    
    # ✅ YANGI QO'SHILDI: Qarzdorlar ro'yxati (to'lov qoldig'i borlar)
    debtor_orders = Order.objects.filter(
        total_amount__gt=F('paid_amount'),
        status__in=['measuring', 'processing', 'installing', 'installed'] # Bekor qilinganlar kerak emas
    ).select_related('customer').order_by('created_at')

    # ✅ YANGI QO'SHILDI: O'rnatish muddati o'tgan buyurtmalar
    overdue_installations = Order.objects.filter(
        installation_scheduled_date__isnull=False,
        installation_scheduled_date__lt=timezone.now()
    ).exclude(
        status__in=['installed', 'cancelled']
    ).select_related('customer').order_by('installation_scheduled_date')
    
    context = {
        'recent_orders': recent_orders,
        'stats': stats,
        'month_stats': month_stats,
        'debtor_orders': debtor_orders,  # ✅ Kontekstga qo'shildi
        'overdue_installations': overdue_installations, # ✅ Kontekstga qo'shildi
        'page_title': 'Dashboard'
    }
    
    return render(request, 'dashboard.html', context)


def login_view(request):
    """Login sahifasi"""
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(
                        request, 
                        f'Xush kelibsiz, {user.get_full_name() or user.username}!'
                    )
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Sizning hisobingiz faol emas!')
            else:
                messages.error(request, 'Foydalanuvchi nomi yoki parol noto\'g\'ri!')
        else:
            messages.error(request, 'Foydalanuvchi nomi va parolni kiriting!')
    
    return render(request, 'accounts/login.html')


@login_required
def user_logout(request):
    """Foydalanuvchi chiqishi"""
    logout(request)
    messages.success(request, 'Tizimdan muvaffaqiyatli chiqdingiz!')
    return redirect('login')

@login_required
def logout_view(request):
    """Logout"""
    
    user_name = request.user.get_full_name()
    logout(request)
    messages.info(request, f'{user_name}, tizimdan muvaffaqiyatli chiqdingiz!')
    return redirect('login')


@login_required
def profile(request):
    """Foydalanuvchi profili"""
    
    user = request.user
    
    # Foydalanuvchi statistikalari
    user_stats = {}
    
    if user.is_technical:
        # ✅ TUZATILDI: To'g'ri field nomlarini ishlatish
        user_stats = {
            'assigned_orders': Order.objects.filter(
                Q(assigned_measurer=user) |
                Q(assigned_manufacturer=user) |
                Q(assigned_installer=user)
            ).count(),
            'completed_tasks': Order.objects.filter(
                Q(assigned_measurer=user) |
                Q(assigned_manufacturer=user) |
                Q(assigned_installer=user),
                status='installed'
            ).count(),
            'active_tasks': Order.objects.filter(
                Q(assigned_measurer=user) |
                Q(assigned_manufacturer=user) |
                Q(assigned_installer=user)
            ).exclude(status__in=['installed', 'cancelled']).count(),
        }
    elif user.is_manager or user.is_admin:
        # Menejer/Admin statistikalari
        user_stats = {
            'total_orders_managed': Order.objects.count(),
            'total_customers': Customer.objects.count(),
            'total_revenue': Payment.objects.filter(
                status='confirmed'
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
    
    context = {
        'user': user,
        'user_stats': user_stats,
        'title': 'Mening profilim'
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password(request):
    """Parol o'zgartirish"""
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validatsiya
        if not request.user.check_password(current_password):
            messages.error(request, 'Joriy parol noto\'g\'ri!')
        elif new_password != confirm_password:
            messages.error(request, 'Yangi parollar mos kelmaydi!')
        elif len(new_password) < 6:
            messages.error(request, 'Parol kamida 6 ta belgidan iborat bo\'lishi kerak!')
        else:
            # Parolni o'zgartirish
            request.user.set_password(new_password)
            request.user.save()
            
            messages.success(request, 'Parol muvaffaqiyatli o\'zgartirildi!')
            return redirect('profile')
    
    context = {
        'title': 'Parol o\'zgartirish'
    }
    
    return render(request, 'accounts/change_password.html', context)


@login_required
def get_dashboard_stats(request):
    """AJAX orqali dashboard statistikalarini olish"""
    
    stats = {
        'total_orders': Order.objects.count(),
        'measuring_orders': Order.objects.filter(status='measuring').count(),
        'processing_orders': Order.objects.filter(status='processing').count(),
        'installing_orders': Order.objects.filter(status='installing').count(),
        'completed_orders': Order.objects.filter(status='installed').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
        'total_customers': Customer.objects.count(),
        'total_revenue': float(Payment.objects.filter(
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0),
    }
    
    return JsonResponse(stats)