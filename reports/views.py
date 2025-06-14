# reports/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
from decimal import Decimal

from customers.models import Customer
from orders.models import Order, OrderItem
from payments.models import Payment
from accounts.models import User


def decimal_to_float(obj):
    """Decimal qiymatlarni float ga o'zgartirish"""
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


@login_required
def report_dashboard(request):
    """
    Hisobotlar asosiy sahifasi
    """
    # Faqat menejer va admin ko'ra oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda hisobotlarni ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    # Asosiy statistikalar
    today = timezone.now().date()
    this_week_start = today - timedelta(days=today.weekday())
    this_month_start = today.replace(day=1)
    
    stats = {
        'total_customers': Customer.objects.count(),
        'total_orders': Order.objects.count(),
        'total_revenue': decimal_to_float(Payment.objects.filter(is_confirmed=True).aggregate(
            total=Sum('amount'))['total'] or 0),
        'completed_orders': Order.objects.filter(status='installed').count(),
        'pending_orders': Order.objects.filter(status__in=['new', 'measuring', 'processing']).count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
        
        # Bu hafta
        'week_customers': Customer.objects.filter(created_at__gte=this_week_start).count(),
        'week_orders': Order.objects.filter(created_at__gte=this_week_start).count(),
        'week_revenue': decimal_to_float(Payment.objects.filter(
            payment_date__gte=this_week_start, is_confirmed=True
        ).aggregate(total=Sum('amount'))['total'] or 0),
        
        # Bu oy
        'month_customers': Customer.objects.filter(created_at__gte=this_month_start).count(),
        'month_orders': Order.objects.filter(created_at__gte=this_month_start).count(),
        'month_revenue': decimal_to_float(Payment.objects.filter(
            payment_date__gte=this_month_start, is_confirmed=True
        ).aggregate(total=Sum('amount'))['total'] or 0),
        
        # Bugun
        'today_orders': Order.objects.filter(created_at__date=today).count(),
        'today_payments': Payment.objects.filter(payment_date__date=today).count(),
        'today_revenue': decimal_to_float(Payment.objects.filter(
            payment_date__date=today, is_confirmed=True
        ).aggregate(total=Sum('amount'))['total'] or 0),
    }
    
    # Eng faol mijozlar
    top_customers = Customer.objects.annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__payments__amount', filter=Q(orders__payments__is_confirmed=True))
    ).filter(order_count__gt=0).order_by('-total_spent')[:5]
    
    # total_spent ni float ga o'zgartirish
    for customer in top_customers:
        customer.total_spent = decimal_to_float(customer.total_spent or 0)
    
    # Eng mashhur jalyuzi turlari - TO'G'RILANADI
    popular_blinds = OrderItem.objects.values('blind_type').annotate(
        count=Count('id'),
        total_amount=Sum('unit_price') * Sum('quantity')  # ✅ total_price o'rniga
    ).order_by('-count')[:5]
    
    # Yoki yanada to'g'ri:
    popular_blinds_corrected = []
    blind_types = OrderItem.objects.values_list('blind_type', flat=True).distinct()
    
    for blind_type in blind_types:
        items = OrderItem.objects.filter(blind_type=blind_type)
        total_amount = sum(item.total_price() for item in items)  # Method chaqirish
        count = items.count()
        
        popular_blinds_corrected.append({
            'blind_type': blind_type,
            'count': count,
            'total_amount': decimal_to_float(total_amount)
        })
    
    # Count bo'yicha saralash
    popular_blinds_corrected.sort(key=lambda x: x['count'], reverse=True)
    popular_blinds = popular_blinds_corrected[:5]
    
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
            'revenue': decimal_to_float(revenue)
        })
    
    monthly_revenue.reverse()  # Eskidan yangiga
    
    context = {
        'stats': stats,
        'top_customers': top_customers,
        'popular_blinds': popular_blinds,
        'monthly_revenue': monthly_revenue,
        'monthly_revenue_json': json.dumps([m['revenue'] for m in monthly_revenue]),
        'monthly_labels_json': json.dumps([m['month'] for m in monthly_revenue]),
    }
    
    return render(request, 'reports/dashboard.html', context)


@login_required
def customer_report(request):
    """
    Mijozlar hisoboti - TO'G'RILANADI
    """
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda hisobotlarni ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    # Mijozlar statistikasi - TO'G'RILANADI
    customers = Customer.objects.annotate(
        order_count=Count('orders'),
        completed_orders=Count('orders', filter=Q(orders__status='installed')),
        total_spent=Sum('orders__payments__amount', filter=Q(orders__payments__is_confirmed=True))
        # outstanding_balance ni alohida hisoblash kerak
    ).order_by('-total_spent')
    
    # Outstanding balance ni alohida hisoblaymiz
    for customer in customers:
        customer.total_spent = decimal_to_float(customer.total_spent or 0)
        
        # Qarzdorlikni hisoblash
        total_orders_value = 0
        total_paid = 0
        
        for order in customer.orders.exclude(status='cancelled'):
            total_orders_value += order.total_price()  # Method chaqirish
            total_paid += order.total_paid()  # Method chaqirish
        
        customer.outstanding_balance = decimal_to_float(max(total_orders_value - total_paid, 0))
    
    # Umumiy statistika
    total_customers = customers.count()
    active_customers = customers.filter(order_count__gt=0).count()
    paying_customers = [c for c in customers if c.total_spent > 0]
    
    # Top 10 mijozlar
    top_customers = [c for c in customers if c.order_count > 0][:10]
    
    # Qarzdor mijozlar
    debtor_customers = [c for c in customers if c.outstanding_balance > 0]
    debtor_customers.sort(key=lambda x: x.outstanding_balance, reverse=True)
    debtor_customers = debtor_customers[:10]
    
    context = {
        'total_customers': total_customers,
        'active_customers': active_customers,
        'paying_customers': len(paying_customers),
        'top_customers': top_customers,
        'debtor_customers': debtor_customers,
    }
    
    return render(request, 'reports/customers.html', context)


@login_required
def order_report(request):
    """
    Buyurtmalar hisoboti - TO'G'RILANADI
    """
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda hisobotlarni ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    # Sana filtri
    period = request.GET.get('period', 'month')
    today = timezone.now().date()
    
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        period_name = "Bu hafta"
    elif period == 'month':
        start_date = today.replace(day=1)
        period_name = "Bu oy"
    else:  # year
        start_date = today.replace(month=1, day=1)
        period_name = "Bu yil"
    
    # Buyurtmalar statistikasi - TO'G'RILANADI
    orders = Order.objects.filter(created_at__gte=start_date)
    
    # Total value ni alohida hisoblash
    total_value = 0
    total_count = 0
    
    for order in orders:
        order_total = order.total_price()  # Method chaqirish
        total_value += order_total
        if order_total > 0:
            total_count += 1
    
    avg_value = total_value / total_count if total_count > 0 else 0
    
    stats = {
        'total_orders': orders.count(),
        'new_orders': orders.filter(status='new').count(),
        'measuring_orders': orders.filter(status='measuring').count(),
        'processing_orders': orders.filter(status='processing').count(),
        'completed_orders': orders.filter(status='installed').count(),
        'cancelled_orders': orders.filter(status='cancelled').count(),
        'total_value': decimal_to_float(total_value),
        'avg_order_value': decimal_to_float(avg_value),
    }
    
    # Kunlik statistika (oxirgi 30 kun)
    daily_stats = []
    for i in range(30):
        date = today - timedelta(days=i)
        daily_orders = Order.objects.filter(created_at__date=date).count()
        daily_revenue = Payment.objects.filter(
            payment_date__date=date, is_confirmed=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        daily_stats.append({
            'date': date.strftime('%d.%m'),
            'orders': daily_orders,
            'revenue': decimal_to_float(daily_revenue)
        })
    
    daily_stats.reverse()
    
    # Eng yaxshi xodimlar
    top_employees = User.objects.filter(
        role__in=['manager', 'technician']
    ).annotate(
        orders_created_count=Count('created_orders', filter=Q(created_orders__created_at__gte=start_date))
    ).order_by('-orders_created_count')[:5]
    
    context = {
        'stats': stats,
        'period': period,
        'period_name': period_name,
        'daily_stats': daily_stats,
        'daily_orders_json': json.dumps([d['orders'] for d in daily_stats]),
        'daily_revenue_json': json.dumps([d['revenue'] for d in daily_stats]),
        'daily_labels_json': json.dumps([d['date'] for d in daily_stats]),
        'top_employees': top_employees,
    }
    
    return render(request, 'reports/orders.html', context)


@login_required
def payment_report(request):
    """
    To'lovlar hisoboti
    """
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda hisobotlarni ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    # Sana filtri
    today = timezone.now().date()
    start_date = today.replace(day=1)  # Bu oy
    
    # To'lovlar statistikasi
    payments = Payment.objects.filter(payment_date__gte=start_date, is_confirmed=True)
    
    total_amount = payments.aggregate(total=Sum('amount'))['total']
    advance_amount = payments.filter(payment_type='advance').aggregate(total=Sum('amount'))['total']
    partial_amount = payments.filter(payment_type='partial').aggregate(total=Sum('amount'))['total']
    final_amount = payments.filter(payment_type='final').aggregate(total=Sum('amount'))['total']
    avg_payment = payments.aggregate(avg=Avg('amount'))['avg']
    
    stats = {
        'total_payments': payments.count(),
        'total_amount': decimal_to_float(total_amount or 0),
        'advance_payments': decimal_to_float(advance_amount or 0),
        'partial_payments': decimal_to_float(partial_amount or 0),
        'final_payments': decimal_to_float(final_amount or 0),
        'avg_payment': decimal_to_float(avg_payment or 0),
    }
    
    # To'lov usullari statistikasi
    payment_methods = payments.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    for method in payment_methods:
        method['total'] = decimal_to_float(method['total'] or 0)
    
    # Eng faol kassirlar
    top_cashiers = User.objects.filter(
        received_payments__payment_date__gte=start_date,
        received_payments__is_confirmed=True
    ).annotate(
        payment_count=Count('received_payments'),
        total_received=Sum('received_payments__amount')
    ).order_by('-total_received')[:5]
    
    for cashier in top_cashiers:
        cashier.total_received = decimal_to_float(cashier.total_received or 0)
    
    # Kunlik to'lovlar (oxirgi 30 kun)
    daily_payments = []
    for i in range(30):
        date = today - timedelta(days=i)
        daily_amount = Payment.objects.filter(
            payment_date__date=date, is_confirmed=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        daily_payments.append({
            'date': date.strftime('%d.%m'),
            'amount': decimal_to_float(daily_amount)
        })
    
    daily_payments.reverse()
    
    context = {
        'stats': stats,
        'payment_methods': payment_methods,
        'top_cashiers': top_cashiers,
        'daily_payments': daily_payments,
        'daily_amounts_json': json.dumps([d['amount'] for d in daily_payments]),
        'daily_labels_json': json.dumps([d['date'] for d in daily_payments]),
    }
    
    return render(request, 'reports/payments.html', context)


@login_required
def financial_report(request):
    """
    Moliyaviy hisobot - TO'G'RILANADI
    """
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda hisobotlarni ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    
    # Bu oylik moliyaviy ma'lumotlar
    this_month_revenue = Payment.objects.filter(
        payment_date__gte=this_month_start, is_confirmed=True
    ).aggregate(total=Sum('amount'))['total']
    
    # Orders value ni alohida hisoblash
    this_month_orders = Order.objects.filter(created_at__gte=this_month_start)
    this_month_orders_value = sum(order.total_price() for order in this_month_orders)
    
    this_month = {
        'revenue': decimal_to_float(this_month_revenue or 0),
        'orders_value': decimal_to_float(this_month_orders_value),
        'completed_orders': Order.objects.filter(
            status='installed', installation_date__gte=this_month_start
        ).count(),
    }
    
    # O'tgan oylik moliyaviy ma'lumotlar
    last_month_revenue = Payment.objects.filter(
        payment_date__gte=last_month_start,
        payment_date__lte=last_month_end,
        is_confirmed=True
    ).aggregate(total=Sum('amount'))['total']
    
    last_month_orders = Order.objects.filter(
        created_at__gte=last_month_start,
        created_at__lte=last_month_end
    )
    last_month_orders_value = sum(order.total_price() for order in last_month_orders)
    
    last_month = {
        'revenue': decimal_to_float(last_month_revenue or 0),
        'orders_value': decimal_to_float(last_month_orders_value),
        'completed_orders': Order.objects.filter(
            status='installed',
            installation_date__gte=last_month_start,
            installation_date__lte=last_month_end
        ).count(),
    }
    
    # O'sish foizlari
    growth = {
        'revenue': ((this_month['revenue'] - last_month['revenue']) / last_month['revenue'] * 100) if last_month['revenue'] > 0 else 0,
        'orders_value': ((this_month['orders_value'] - last_month['orders_value']) / last_month['orders_value'] * 100) if last_month['orders_value'] > 0 else 0,
        'completed_orders': ((this_month['completed_orders'] - last_month['completed_orders']) / last_month['completed_orders'] * 100) if last_month['completed_orders'] > 0 else 0,
    }
    
    # Qarzdorlik ma'lumotlari - TO'G'RILANADI
    outstanding_orders = []
    
    for order in Order.objects.filter(status__in=['new', 'measuring', 'processing', 'installed']):
        total_price = order.total_price()
        total_paid = order.total_paid()
        remaining = max(total_price - total_paid, 0)
        
        if remaining > 0:
            outstanding_orders.append({
                'order': order,
                'total_price': decimal_to_float(total_price),
                'total_paid': decimal_to_float(total_paid),
                'remaining': decimal_to_float(remaining)
            })
    
    # Remaining bo'yicha saralash
    outstanding_orders.sort(key=lambda x: x['remaining'], reverse=True)
    outstanding_orders = outstanding_orders[:10]
    
    total_outstanding = sum([order['remaining'] for order in outstanding_orders])
    
    context = {
        'this_month': this_month,
        'last_month': last_month,
        'growth': growth,
        'outstanding_orders': outstanding_orders,
        'total_outstanding': total_outstanding,
    }
    
    return render(request, 'reports/financial.html', context)