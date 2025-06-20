# accounts/views.py - YANGILANGAN VERSIYA

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

# Vaqtincha funksiyani olib tashlaymiz
# def technical_dashboard_temp(request):...


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
    """Admin va menejer uchun dashboard"""
    
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
        
        # Buyurtmalar
        'total_orders': Order.objects.count(),
        'new_orders': Order.objects.filter(status='new').count(),
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
        'month_revenue': Payment.objects.filter(
            payment_date__date__gte=this_month_start,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        
        # Texnik xodimlar
        'total_staff': User.objects.filter(role='technical').count(),
        'active_staff': User.objects.filter(
            role='technical', 
            is_active=True
        ).count(),
    }
    
    # So'nggi buyurtmalar
    recent_orders = Order.objects.select_related('customer').order_by(
        '-created_at'
    )[:10]
    
    # Bugungi vazifalar
    today_tasks = []
    
    # Bugungi o'lchov vazifalari
    measuring_today = Order.objects.filter(
        status='measuring',
        measurement_date__date=today
    ).select_related('customer', 'assigned_measurer')
    
    for order in measuring_today:
        today_tasks.append({
            'type': 'measurement',
            'order': order,
            'assigned_to': order.assigned_measurer,
            'time': order.measurement_date,
            'icon': 'bi-rulers',
            'color': 'info'
        })
    
    # Bugungi o'rnatish vazifalari
    installing_today = Order.objects.filter(
        status='installing',
        installation_date__date=today
    ).select_related('customer', 'assigned_installer')
    
    for order in installing_today:
        today_tasks.append({
            'type': 'installation',
            'order': order,
            'assigned_to': order.assigned_installer,
            'time': order.installation_date,
            'icon': 'bi-tools',
            'color': 'success'
        })
    
    # Kechikkan vazifalar
    overdue_tasks = []
    
    # Kechikkan o'lchovlar
    overdue_measuring = Order.objects.filter(
        status='measuring',
        measurement_date__lt=current_time
    ).select_related('customer', 'assigned_measurer')
    overdue_tasks.extend(overdue_measuring)
    
    # Kechikkan o'rnatishlar
    overdue_installing = Order.objects.filter(
        status='installing',
        installation_date__lt=current_time
    ).select_related('customer', 'assigned_installer')
    overdue_tasks.extend(overdue_installing)
    
    # So'nggi to'lovlar
    recent_payments = Payment.objects.select_related(
        'order__customer'
    ).order_by('-payment_date')[:10]
    
    # Kutilayotgan to'lovlar (PaymentSchedule dan)
    pending_payments = []
    try:
        from payments.models import PaymentSchedule
        pending_payments = PaymentSchedule.objects.filter(
            is_paid=False
        ).select_related('order__customer').order_by('due_date')[:10]
    except Exception:
        # Agar PaymentSchedule modeli mavjud bo'lmasa
        pending_payments = []
    
    # Top mijozlar (buyurtmalar soni bo'yicha)
    top_customers = Customer.objects.annotate(
        order_count=Count('orders')
    ).filter(order_count__gt=0).order_by('-order_count')[:5]
    
    # Grafik uchun ma'lumotlar (so'nggi 7 kun)
    chart_data = []
    for i in range(7):
        chart_date = today - timedelta(days=6-i)
        daily_revenue = Payment.objects.filter(
            payment_date__date=chart_date,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        chart_data.append({
            'date': chart_date.strftime('%d.%m'),
            'revenue': float(daily_revenue)
        })
    
    context = {
        'stats': stats,
        'recent_orders': recent_orders,
        'today_tasks': today_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_payments': recent_payments,
        'pending_payments': pending_payments,
        'top_customers': top_customers,
        'chart_data': chart_data,
        'current_time': current_time,
        'user': request.user,
        'title': 'Dashboard'
    }
    
    return render(request, 'accounts/manager_dashboard.html', context)


@login_required
def profile(request):
    """Foydalanuvchi profili"""
    
    user = request.user
    
    # Foydalanuvchi statistikasi
    user_stats = {}
    
    if user.is_technical:
        # Texnik xodim statistikasi
        user_stats = {
            'total_tasks': 0,  # Keyinroq hisoblash qo'shamiz
            'completed_tasks': 0,
            'active_tasks': 0,
            'this_month_completed': 0,
        }
    
    elif user.is_manager or user.is_admin:
        # Menejer/Admin statistikasi  
        user_stats = {
            'created_orders': 0,  # Keyinroq hisoblash qo'shamiz
            'managed_payments': 0,
        }
    
    context = {
        'user': user,
        'user_stats': user_stats,
        'title': 'Mening profilim'
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password(request):
    """Parolni o'zgartirish"""
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Joriy parol noto\'g\'ri!')
        elif new_password1 != new_password2:
            messages.error(request, 'Yangi parollar mos kelmaydi!')
        elif len(new_password1) < 8:
            messages.error(request, 'Parol kamida 8 ta belgidan iborat bo\'lishi kerak!')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            messages.success(request, 'Parol muvaffaqiyatli o\'zgartirildi!')
            return redirect('profile')
    
    context = {
        'title': 'Parolni o\'zgartirish'
    }
    
    return render(request, 'accounts/change_password.html', context)


# AJAX view'lar

@login_required
def get_dashboard_stats(request):
    """Dashboard statistikasi (AJAX uchun)"""
    from django.http import JsonResponse
    
    if not (request.user.is_manager or request.user.is_admin):
        return JsonResponse({'error': 'Permission denied'})
    
    today = date.today()
    stats = {
        'orders': {
            'new': Order.objects.filter(status='new').count(),
            'measuring': Order.objects.filter(status='measuring').count(),
            'processing': Order.objects.filter(status='processing').count(),
            'installing': Order.objects.filter(status='installing').count(),
            'completed': Order.objects.filter(status='installed').count(),
        },
        'revenue': {
            'today': float(Payment.objects.filter(
                payment_date__date=today,
                status='confirmed'
            ).aggregate(total=Sum('amount'))['total'] or 0),
            'total': float(Payment.objects.filter(
                status='confirmed'
            ).aggregate(total=Sum('amount'))['total'] or 0),
        },
        'customers': Customer.objects.count(),
        'staff': User.objects.filter(role='technical', is_active=True).count(),
    }
    
    return JsonResponse(stats)