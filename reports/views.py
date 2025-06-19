# reports/views.py - TO'LIQ TO'G'IRLANGAN VERSIYA

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
    Hisobotlar asosiy sahifasi - TO'G'IRLANGAN
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
    
    # ✅ TO'G'RILANDI: Eng mashhur jalyuzi turlari
    popular_blinds = []
    blind_types = OrderItem.objects.values_list('blind_type', flat=True).distinct()
    
    for blind_type in blind_types:
        items = OrderItem.objects.filter(blind_type=blind_type)
        count = items.count()
        
        # Total amount ni to'g'ri hisoblash
        total_amount = 0
        for item in items:
            total_amount += item.total_price()  # Method chaqirish
        
        popular_blinds.append({
            'blind_type': blind_type,
            'blind_type_display': dict(OrderItem.BLIND_TYPE_CHOICES).get(blind_type, blind_type),
            'count': count,
            'total_amount': decimal_to_float(total_amount)
        })
    
    # Eng ko'p sotilgan turlari bo'yicha saralash
    popular_blinds.sort(key=lambda x: x['count'], reverse=True)
    popular_blinds = popular_blinds[:5]
    
    # Status bo'yicha taqsimlash
    status_distribution = []
    for status_code, status_name in Order.STATUS_CHOICES:
        count = Order.objects.filter(status=status_code).count()
        status_distribution.append({
            'status': status_code,
            'status_display': status_name,
            'count': count
        })
    
    # JSON formatga o'tkazish (JavaScript uchun)
    charts_data = {
        'status_labels': [item['status_display'] for item in status_distribution],
        'status_data': [item['count'] for item in status_distribution],
        'blinds_labels': [item['blind_type_display'] for item in popular_blinds],
        'blinds_data': [item['count'] for item in popular_blinds],
    }
    
    context = {
        'stats': stats,
        'top_customers': top_customers,
        'popular_blinds': popular_blinds,
        'status_distribution': status_distribution,
        'charts_data': json.dumps(charts_data),
    }
    
    return render(request, 'reports/dashboard.html', context)


@login_required
def financial_report(request):
    """
    Moliyaviy hisobot - TO'G'IRLANGAN
    """
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda moliyaviy hisobotni ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    # Sana filtri
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    
    # Bu oylik ma'lumotlar
    this_month_orders = Order.objects.filter(created_at__gte=this_month_start)
    this_month_payments = Payment.objects.filter(
        payment_date__gte=this_month_start,
        is_confirmed=True
    )
    
    # ✅ TO'G'RILANDI: Total value ni alohida hisoblash
    this_month_total_value = 0
    for order in this_month_orders:
        this_month_total_value += order.total_price()  # Method chaqirish
    
    this_month = {
        'orders_count': this_month_orders.count(),
        'total_value': decimal_to_float(this_month_total_value),
        'total_received': decimal_to_float(this_month_payments.aggregate(
            total=Sum('amount'))['total'] or 0),
    }
    
    # O'tgan oylik ma'lumotlar
    last_month_orders = Order.objects.filter(
        created_at__gte=last_month_start,
        created_at__lte=last_month_end
    )
    last_month_payments = Payment.objects.filter(
        payment_date__gte=last_month_start,
        payment_date__lte=last_month_end,
        is_confirmed=True
    )
    
    # ✅ TO'G'RILANDI: O'tgan oy total value
    last_month_total_value = 0
    for order in last_month_orders:
        last_month_total_value += order.total_price()  # Method chaqirish
    
    last_month = {
        'orders_count': last_month_orders.count(),
        'total_value': decimal_to_float(last_month_total_value),
        'total_received': decimal_to_float(last_month_payments.aggregate(
            total=Sum('amount'))['total'] or 0),
    }
    
    # O'sish foizi
    def calculate_growth(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100
    
    growth = {
        'orders': calculate_growth(this_month['orders_count'], last_month['orders_count']),
        'value': calculate_growth(this_month['total_value'], last_month['total_value']),
        'received': calculate_growth(this_month['total_received'], last_month['total_received']),
    }
    
    # ✅ TO'G'RILANDI: Qarzdorlik ma'lumotlari
    outstanding_orders = []
    
    for order in Order.objects.filter(status__in=['new', 'measuring', 'processing', 'installed']):
        total_price = order.total_price()  # Method chaqirish
        total_paid = order.total_paid()    # Method chaqirish
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


@login_required
def orders_report(request):
    """
    Buyurtmalar hisoboti - TO'G'IRLANGAN
    """
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda buyurtmalar hisobotini ko\'rish huquqi yo\'q!')
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
    
    # ✅ TO'G'IRLANDI: Buyurtmalar statistikasi
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
    
    daily_stats.reverse()  # Eskidan yangiga
    
    # Jalyuzi turlari bo'yicha statistika
    blind_stats = []
    for blind_type, blind_name in OrderItem.BLIND_TYPE_CHOICES:
        items = OrderItem.objects.filter(
            blind_type=blind_type,
            order__created_at__gte=start_date
        )
        count = items.count()
        
        # Total amount ni to'g'ri hisoblash
        total_amount = 0
        for item in items:
            total_amount += item.total_price()
        
        if count > 0:
            blind_stats.append({
                'type': blind_name,
                'count': count,
                'total_amount': decimal_to_float(total_amount),
                'avg_price': decimal_to_float(total_amount / count) if count > 0 else 0
            })
    
    # Eng ko'p sotilgan turlari bo'yicha saralash
    blind_stats.sort(key=lambda x: x['count'], reverse=True)
    
    context = {
        'period_name': period_name,
        'period': period,
        'stats': stats,
        'daily_stats': daily_stats,
        'blind_stats': blind_stats,
        'charts_data': json.dumps({
            'daily_labels': [item['date'] for item in daily_stats],
            'daily_orders': [item['orders'] for item in daily_stats],
            'daily_revenue': [item['revenue'] for item in daily_stats],
        }),
    }
    
    return render(request, 'reports/orders.html', context)


@login_required
def customers_report(request):
    """
    Mijozlar hisoboti
    """
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda mijozlar hisobotini ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    # Asosiy statistikalar
    total_customers = Customer.objects.count()
    active_customers = Customer.objects.filter(orders__isnull=False).distinct().count()
    
    # Eng faol mijozlar
    top_customers = Customer.objects.annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__payments__amount', filter=Q(orders__payments__is_confirmed=True))
    ).filter(order_count__gt=0).order_by('-order_count')[:10]
    
    # total_spent ni float ga o'zgartirish
    for customer in top_customers:
        customer.total_spent = decimal_to_float(customer.total_spent or 0)
    
    # Kategoriya bo'yicha taqsimlash
    category_stats = []
    for category_code, category_name in Customer.CATEGORY_CHOICES:
        count = Customer.objects.filter(category=category_code).count()
        category_stats.append({
            'category': category_name,
            'count': count
        })
    
    # Yaqinda qo'shilgan mijozlar (oxirgi 30 kun)
    recent_customers = Customer.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:10]
    
    context = {
        'total_customers': total_customers,
        'active_customers': active_customers,
        'inactive_customers': total_customers - active_customers,
        'top_customers': top_customers,
        'category_stats': category_stats,
        'recent_customers': recent_customers,
    }
    
    return render(request, 'reports/customers.html', context)


# ✅ QO'SHILDI: payment_report funksiyasi
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
    prepayment_amount = payments.filter(payment_type='prepayment').aggregate(total=Sum('amount'))['total']
    partial_amount = payments.filter(payment_type='partial').aggregate(total=Sum('amount'))['total']
    final_amount = payments.filter(payment_type='final').aggregate(total=Sum('amount'))['total']
    avg_payment = payments.aggregate(avg=Avg('amount'))['avg']
    
    stats = {
        'total_payments': payments.count(),
        'total_amount': decimal_to_float(total_amount or 0),
        'prepayment_amount': decimal_to_float(prepayment_amount or 0),
        'partial_amount': decimal_to_float(partial_amount or 0),
        'final_amount': decimal_to_float(final_amount or 0),
        'avg_payment': decimal_to_float(avg_payment or 0),
    }
    
    # To'lov usullari statistikasi
    payment_methods = payments.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    for method in payment_methods:
        method['total'] = decimal_to_float(method['total'] or 0)
        method['method_display'] = dict(Payment.PAYMENT_METHOD_CHOICES).get(method['payment_method'], method['payment_method'])
    
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