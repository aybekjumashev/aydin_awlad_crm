# accounts/views.py - TO'LIQ VERSIYA

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


def login_view(request):
    """
    Login sahifasi
    """
    # Agar foydalanuvchi allaqachon login qilgan bo'lsa, dashboard ga yo'naltirish
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
                        request.session.set_expiry(0)  # Browser yopilganda session o'chadi
                    
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
    """Asosiy dashboard sahifasi"""
    
    current_time = timezone.now()
    today = date.today()
    this_month_start = today.replace(day=1)
    
    # Foydalanuvchi turiga qarab ma'lumotlarni olish
    if request.user.is_technical:
        return technical_dashboard(request)
    else:
        return manager_dashboard(request)


def technical_dashboard(request):
    """Texnik xodim uchun dashboard"""
    
    # Tayinlangan vazifalar
    my_orders = Order.objects.filter(
        Q(assigned_measurer=request.user) |
        Q(assigned_manufacturer=request.user) |
        Q(assigned_installer=request.user)
    ).exclude(status__in=['installed', 'cancelled']).select_related('customer')
    
    # So'nggi 10 ta vazifa
    recent_orders = my_orders.order_by('-created_at')[:10]
    
    # Vazifalar statistikasi
    stats = {
        'my_total_tasks': my_orders.count(),
        'measuring_tasks': my_orders.filter(
            assigned_measurer=request.user, 
            status='measuring'
        ).count() if request.user.can_measure else 0,
        
        'manufacturing_tasks': my_orders.filter(
            assigned_manufacturer=request.user, 
            status='processing'
        ).count() if request.user.can_manufacture else 0,
        
        'installation_tasks': my_orders.filter(
            assigned_installer=request.user, 
            status='installing'
        ).count() if request.user.can_install else 0,
    }
    
    # Bugungi vazifalar
    today_tasks = []
    
    # Bugungi o'lchov vazifalari
    if request.user.can_measure:
        measuring_today = my_orders.filter(
            assigned_measurer=request.user,
            status='measuring',
            measurement_date__date=date.today()
        )
        for order in measuring_today:
            today_tasks.append({
                'order': order,
                'task_type': 'measure',
                'task_name': 'O\'lchov olish',
                'time': order.measurement_date
            })
    
    # Bugungi o'rnatish vazifalari  
    if request.user.can_install:
        installation_today = my_orders.filter(
            assigned_installer=request.user,
            status='installing',
            installation_date__date=date.today()
        )
        for order in installation_today:
            today_tasks.append({
                'order': order,
                'task_type': 'install',
                'task_name': 'O\'rnatish',
                'time': order.installation_date
            })
    
    # Bildirishnomalar
    notifications = []
    
    # Kechikkan vazifalar
    overdue_orders = my_orders.filter(
        Q(measurement_date__lt=timezone.now(), status='measuring') |
        Q(installation_date__lt=timezone.now(), status='installing')
    )
    
    if overdue_orders.exists():
        notifications.append({
            'type': 'warning',
            'title': 'Kechikkan vazifalar!',
            'message': f'{overdue_orders.count()} ta vazifa muddatidan kechikdi.'
        })
    
    context = {
        'recent_orders': recent_orders,
        'stats': stats,
        'today_tasks': today_tasks,
        'notifications': notifications,
        'current_time': timezone.now(),
    }
    
    return render(request, 'dashboard.html', context)


def manager_dashboard(request):
    """Menejer/Admin uchun dashboard"""
    
    today = date.today()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    # Asosiy statistikalar
    total_orders = Order.objects.count()
    total_customers = Customer.objects.count()
    
    # Bu oylik statistika
    this_month_orders = Order.objects.filter(created_at__date__gte=this_month_start)
    this_month_revenue = Payment.objects.filter(
        payment_date__date__gte=this_month_start,
        status='confirmed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Status bo'yicha buyurtmalar
    order_stats = {
        'total_orders': total_orders,
        'new_orders': Order.objects.filter(status='new').count(),
        'measuring_orders': Order.objects.filter(status='measuring').count(),
        'processing_orders': Order.objects.filter(status='processing').count(),
        'installing_orders': Order.objects.filter(status='installing').count(),
        'completed_orders': Order.objects.filter(status='installed').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
        'active_orders': Order.objects.exclude(status__in=['installed', 'cancelled']).count(),
    }
    
    # So'nggi buyurtmalar
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
    
    # To'lov statistikasi
    payment_stats = {
        'pending_payments': Order.objects.filter(payment_status='pending').count(),
        'partial_payments': Order.objects.filter(payment_status='partial').count(),
        'paid_orders': Order.objects.filter(payment_status='paid').count(),
        'total_revenue': Payment.objects.filter(status='confirmed').aggregate(
            total=Sum('amount')
        )['total'] or 0,
        'monthly_revenue': this_month_revenue,
    }
    
    # Bildirishnomalar
    notifications = []
    
    # Kechikkan o'lchov vazifalari
    overdue_measurements = Order.objects.filter(
        status='measuring',
        measurement_date__lt=timezone.now()
    )
    if overdue_measurements.exists():
        notifications.append({
            'type': 'warning',
            'title': 'Kechikkan o\'lchov vazifalari!',
            'message': f'{overdue_measurements.count()} ta o\'lchov muddatidan kechikdi.'
        })
    
    # To'lanmagan buyurtmalar (1 haftadan ortiq)
    week_ago = timezone.now() - timedelta(days=7)
    unpaid_orders = Order.objects.filter(
        payment_status='pending',
        created_at__lt=week_ago
    )
    if unpaid_orders.exists():
        notifications.append({
            'type': 'danger',
            'title': 'To\'lanmagan buyurtmalar!',
            'message': f'{unpaid_orders.count()} ta buyurtma 1 haftadan ortiq to\'lanmagan.'
        })
    
    # Bugungi rejalar
    today_measurements = Order.objects.filter(
        measurement_date__date=today
    ).select_related('customer', 'assigned_measurer')
    
    today_installations = Order.objects.filter(
        installation_date__date=today
    ).select_related('customer', 'assigned_installer')
    
    if today_measurements.exists() or today_installations.exists():
        notifications.append({
            'type': 'info',
            'title': 'Bugungi rejalar',
            'message': f'Bugun {today_measurements.count()} ta o\'lchov va {today_installations.count()} ta o\'rnatish rejalashtirilgan.'
        })
    
    # Barcha statistika
    stats = {
        **order_stats,
        **payment_stats,
        'total_customers': total_customers,
    }
    
    context = {
        'recent_orders': recent_orders,
        'stats': stats,
        'notifications': notifications,
        'current_time': timezone.now(),
        'today_measurements': today_measurements,
        'today_installations': today_installations,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def profile_view(request):
    """
    Foydalanuvchi profili
    """
    user = request.user
    
    # Foydalanuvchi statistikasi
    if user.is_technical:
        # Texnik xodim statistikasi
        personal_stats = {
            'assigned_orders': user.get_assigned_orders_count(),
            'completed_measurements': Order.objects.filter(
                assigned_measurer=user,
                status__in=['processing', 'installing', 'installed']
            ).count() if user.can_measure else 0,
            'completed_manufacturing': Order.objects.filter(
                assigned_manufacturer=user,
                status__in=['installing', 'installed']
            ).count() if user.can_manufacture else 0,
            'completed_installations': Order.objects.filter(
                assigned_installer=user,
                status='installed'
            ).count() if user.can_install else 0,
        }
    else:
        # Manager/Admin statistikasi
        personal_stats = {
            'total_orders_managed': Order.objects.count(),
            'total_customers': Customer.objects.count(),
            'total_payments_received': Payment.objects.filter(
                status='confirmed'
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
    
    context = {
        'user': user,
        'personal_stats': personal_stats,
    }
    
    return render(request, 'accounts/profile.html', context)