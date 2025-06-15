# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json

from customers.models import Customer
from orders.models import Order, OrderItem
from payments.models import Payment
from accounts.models import User


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
    
    context = {'stats': stats}
    
    # Role-specific ma'lumotlar
    if user.is_manager() or user.is_admin():
        # Bu oylik statistika
        monthly_stats = {
            'new_customers': Customer.objects.filter(created_at__gte=this_month_start).count(),
            'new_orders': Order.objects.filter(created_at__gte=this_month_start).count(),
            'completed_orders': Order.objects.filter(
                status='installed',
                installation_date__gte=this_month_start
            ).count(),
            'total_revenue': Payment.objects.filter(
                is_confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'month_revenue': Payment.objects.filter(
                payment_date__gte=this_month_start,
                is_confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        # So'nggi buyurtmalar
        recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
        
        context.update({
            'monthly_stats': monthly_stats,
            'recent_orders': recent_orders,
        })
    
    elif user.is_technician():
        # Texnik xodim uchun shaxsiy statistika
        personal_stats = user.get_dashboard_stats()
        context['personal_stats'] = personal_stats
        
        # Faqat o'ziga tegishli buyurtmalar
        recent_orders = Order.objects.filter(
            Q(measured_by=user) |
            Q(processed_by=user) |
            Q(installed_by=user) |
            Q(created_by=user)
        ).distinct().select_related('customer').order_by('-created_at')[:5]
        
        context['recent_orders'] = recent_orders
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    """
    Foydalanuvchi profili
    """
    user = request.user
    
    # Foydalanuvchi statistikasi
    personal_stats = user.get_dashboard_stats()
    
    # Login tarixi (oxirgi 10 ta)
    # Bu qism kelajakda LoginHistory modeli yaratilganda implement qilinadi
    
    context = {
        'user': user,
        'personal_stats': personal_stats,
    }
    
    return render(request, 'accounts/profile.html', context)