# accounts/views.py - YANGILANGAN VERSIYA ("new" status olib tashlandi)

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta, date

from customers.models import Customer
from orders.models import Order, OrderItem
from payments.models import Payment
from .models import User
from .technical_views import technical_dashboard


def login_view(request):
    """
    Login sahifasi
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # "Meni eslab qol" funksiyasi
                    if not remember_me:
                        request.session.set_expiry(0)
                    
                    messages.success(request, f'Xush kelibsiz, {user.get_full_name()}!')
                    
                    # next parametri bo'yicha yo'naltirish
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    else:
                        return redirect('dashboard')
                else:
                    messages.error(request, 'Sizning hisobingiz bloklangan!')
            else:
                messages.error(request, 'Foydalanuvchi nomi yoki parol noto\'g\'ri!')
        else:
            messages.error(request, 'Foydalanuvchi nomi va parolni kiriting!')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """
    Logout
    """
    user_name = request.user.get_full_name()
    logout(request)
    messages.info(request, f'{user_name}, tizimdan muvaffaqiyatli chiqdingiz!')
    return redirect('login')


@login_required
def dashboard(request):
    """Asosiy dashboard sahifasi - foydalanuvchi turiga qarab"""
    
    # Texnik xodim uchun maxsus dashboard
    if request.user.is_technical:
        return technical_dashboard(request)
    
    # Admin va menejer uchun umumiy dashboard
    return manager_dashboard(request)


def manager_dashboard(request):
    """Admin va menejer uchun dashboard (new status olib tashlandi)"""
    
    current_time = timezone.now()
    today = date.today()
    this_month_start = today.replace(day=1)
    this_week_start = today - timedelta(days=today.weekday())
    
    # Asosiy statistika
    stats = {
        # Mijozlar
        'total_customers': Customer.objects.count(),
        'new_customers_today': Customer.objects.filter(
            created_at__date=today
        ).count(),
        'new_customers_week': Customer.objects.filter(
            created_at__date__gte=this_week_start
        ).count(),
        'new_customers_month': Customer.objects.filter(
            created_at__date__gte=this_month_start
        ).count(),
        
        # Buyurtmalar ("new" status olib tashlandi)
        'total_orders': Order.objects.count(),
        'measuring_orders': Order.objects.filter(status='measuring').count(),
        'processing_orders': Order.objects.filter(status='processing').count(),
        'installing_orders': Order.objects.filter(status='installing').count(),
        'completed_orders': Order.objects.filter(status='installed').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
        
        # To'lovlar
        'total_revenue': Payment.objects.filter(
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'pending_payments': Payment.objects.filter(
            status='pending'
        ).count(),
        'today_revenue': Payment.objects.filter(
            payment_date__date=today,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # So'nggi buyurtmalar
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
    
    # So'nggi to'lovlar
    recent_payments = Payment.objects.select_related(
        'order', 'order__customer'
    ).filter(status='confirmed').order_by('-payment_date')[:10]
    
    # Bu hafta statistikasi
    week_stats = {
        'orders': Order.objects.filter(created_at__date__gte=this_week_start).count(),
        'revenue': Payment.objects.filter(
            payment_date__date__gte=this_week_start,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'customers': Customer.objects.filter(
            created_at__date__gte=this_week_start
        ).count(),
    }
    
    # Bu oy statistikasi
    month_stats = {
        'orders': Order.objects.filter(created_at__date__gte=this_month_start).count(),
        'revenue': Payment.objects.filter(
            payment_date__date__gte=this_month_start,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'customers': Customer.objects.filter(
            created_at__date__gte=this_month_start
        ).count(),
    }
    
    # Texnik xodimlar statistikasi
    technical_stats = User.objects.filter(role='technical').aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(is_active=True)),
        measurers=Count('id', filter=Q(can_measure=True, is_active=True)),
        manufacturers=Count('id', filter=Q(can_manufacture=True, is_active=True)),
        installers=Count('id', filter=Q(can_install=True, is_active=True)),
    )
    
    context = {
        'stats': stats,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'week_stats': week_stats,
        'month_stats': month_stats,
        'technical_stats': technical_stats,
        'title': 'Bosh sahifa'
    }
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile(request):
    """Foydalanuvchi profili"""
    
    user = request.user
    
    # Foydalanuvchi statistikalari
    user_stats = {}
    
    if user.is_technical:
        # Texnik xodim statistikalari
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
    elif user.is_manager() or user.is_admin():
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
    
    from django.http import JsonResponse
    
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