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
                payment_date__gte=this_month_start,
                is_confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        # Bugungi statistika
        daily_stats = {
            'today_orders': Order.objects.filter(created_at__date=today).count(),
            'today_payments': Payment.objects.filter(payment_date__date=today).count(),
            'today_revenue': Payment.objects.filter(
                payment_date__date=today, is_confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        # Eng faol mijozlar
        top_customers = Customer.objects.annotate(
            order_count=Count('orders'),
            total_spent=Sum('orders__payments__amount', filter=Q(orders__payments__is_confirmed=True))
        ).filter(order_count__gt=0).order_by('-total_spent')[:5]
        
        # Decimal qiymatlarni float ga o'zgartirish
        for customer in top_customers:
            customer.total_spent = float(customer.total_spent or 0)
        
        # Eng mashhur jalyuzi turlari
        popular_blinds = OrderItem.objects.values('blind_type').annotate(
            count=Count('id'),
            total_amount=Sum('total_price')
        ).order_by('-count')[:5]
        
        # total_amount ni float ga o'zgartirish
        for blind in popular_blinds:
            blind['total_amount'] = float(blind['total_amount'] or 0)
        
        # Oylik daromad grafigi (oxirgi 6 oy)
        monthly_revenue = []
        for i in range(6):
            month_start = (today.replace(day=1) - timedelta(days=32*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            revenue = Payment.objects.filter(
                payment_date__date__gte=month_start,
                payment_date__date__lte=month_end,
                is_confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_revenue.append({
                'month': month_start.strftime('%B %Y'),
                'revenue': float(revenue)
            })
        
        monthly_revenue.reverse()  # Eskidan yangiga
        
        # So'nggi buyurtmalar va to'lovlar
        recent_orders = Order.objects.select_related('customer', 'created_by').order_by('-created_at')[:5]
        recent_payments = Payment.objects.select_related('order__customer', 'received_by').order_by('-payment_date')[:5]
        
        # Decimal qiymatlarni float ga o'zgartirish
        monthly_stats['total_revenue'] = float(monthly_stats['total_revenue'])
        daily_stats['today_revenue'] = float(daily_stats['today_revenue'])
        
        context.update({
            'monthly_stats': monthly_stats,
            'daily_stats': daily_stats,
            'recent_orders': recent_orders,
            'recent_payments': recent_payments,
            'top_customers': top_customers,
            'popular_blinds': popular_blinds,
            'monthly_revenue': monthly_revenue,
            'monthly_revenue_json': json.dumps([m['revenue'] for m in monthly_revenue]),
            'monthly_labels_json': json.dumps([m['month'] for m in monthly_revenue]),
        })
    else:
        # Texnik xodim uchun - barcha buyurtmalarni ko'rish
        recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
        
        # Texnik xodim vazifalariga qarab statistika
        my_tasks = {}
        
        if user.can_measure:
            my_tasks['to_measure'] = Order.objects.filter(status='measuring').count()
        
        if user.can_manufacture:
            my_tasks['to_process'] = Order.objects.filter(status='processing').count()
        
        if user.can_install:
            my_tasks['to_install'] = Order.objects.filter(status='processing').count()  # O'rnatishga tayyor
        
        context.update({
            'recent_orders': recent_orders,
            'my_tasks': my_tasks,
        })
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
            'measured_orders': Order.objects.filter(measured_by=user).count() if hasattr(Order, 'measured_by') else 0,
            'processed_orders': Order.objects.filter(processed_by=user).count() if hasattr(Order, 'processed_by') else 0,
            'installed_orders': Order.objects.filter(installed_by=user).count() if hasattr(Order, 'installed_by') else 0,
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
        stats['total_received'] = float(stats['total_received'])
    else:
        stats = {}
    
    context = {
        'user': user,
        'stats': stats,
    }
    
    return render(request, 'accounts/profile.html', context)