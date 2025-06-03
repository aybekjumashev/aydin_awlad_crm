# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta

from customers.models import Customer
from orders.models import Order
from payments.models import Payment


@login_required
def dashboard(request):
    """
    Asosiy dashboard - rol asosida ma'lumotlarni ko'rsatish
    """
    user = request.user
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # Umumiy statistika
    stats = {
        'total_customers': Customer.objects.count(),
        'total_orders': Order.objects.count(),
        'new_orders': Order.objects.filter(status='new').count(),
        'measuring_orders': Order.objects.filter(status='measuring').count(),
        'processing_orders': Order.objects.filter(status='processing').count(),
        'completed_orders': Order.objects.filter(status='installed').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
    }
    
    # Bu oylik statistika
    monthly_stats = {
        'new_customers': Customer.objects.filter(created_at__gte=this_month_start).count(),
        'new_orders': Order.objects.filter(created_at__gte=this_month_start).count(),
        'completed_orders': Order.objects.filter(
            status='installed',
            installation_date__gte=this_month_start
        ).count(),
        'total_revenue': Payment.objects.filter(
            payment_date__gte=this_month_start,
            is_confirmed=True
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # Ro'yxatlar (rol asosida)
    recent_orders = Order.objects.select_related('customer', 'created_by').order_by('-created_at')
    recent_payments = Payment.objects.select_related('order__customer', 'received_by').order_by('-payment_date')[:10]
    
    # Role-specific ma'lumotlar
    if user.is_manager() or user.is_admin():
        # Menejer va Admin uchun - barcha ma'lumotlar
        context = {
            'stats': stats,
            'monthly_stats': monthly_stats,
            'recent_orders': recent_orders[:10],  # Slice-ni context da qilamiz
            'recent_payments': recent_payments,
            'pending_orders': Order.objects.filter(status__in=['new', 'measuring']).count(),
            'overdue_orders': Order.objects.filter(
                status='processing',
                created_at__lt=today - timedelta(days=7)
            ).count(),
        }
    else:
        # Texnik xodim uchun - faqat o'ziga tegishli
        my_orders = recent_orders.filter(
            Q(measured_by=user) | 
            Q(processed_by=user) | 
            Q(installed_by=user)
        )[:10]  # Filter qilib, keyin slice qilamiz
        context = {
            'stats': stats,
            'my_orders': my_orders,
            'my_tasks': {
                'to_measure': Order.objects.filter(status='measuring', measured_by=user).count(),
                'to_process': Order.objects.filter(status='processing', processed_by=user).count(),
                'to_install': Order.objects.filter(status='processing', installed_by=user).count(),
            }
        }
    
    return render(request, 'dashboard.html', context)


def login_view(request):
    """
    Login sahifasi
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Login yoki parol noto\'g\'ri!')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """
    Logout
    """
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    """
    Foydalanuvchi profili
    """
    user = request.user
    
    # Foydalanuvchi statistikasi
    if user.is_technician():
        stats = {
            'measured_orders': Order.objects.filter(measured_by=user).count(),
            'processed_orders': Order.objects.filter(processed_by=user).count(),
            'installed_orders': Order.objects.filter(installed_by=user).count(),
        }
    elif user.is_manager():
        stats = {
            'created_orders': Order.objects.filter(created_by=user).count(),
            'received_payments': Payment.objects.filter(received_by=user).count(),
            'total_received': Payment.objects.filter(
                received_by=user, 
                is_confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
    else:
        stats = {}
    
    context = {
        'user': user,
        'stats': stats,
    }
    
    return render(request, 'accounts/profile.html', context)