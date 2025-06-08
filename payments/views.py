# payments/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Payment
from orders.models import Order
from .forms import PaymentForm


@login_required
def payment_list(request):
    """
    To'lovlar ro'yxati
    """
    # Faqat menejer va admin ko'ra oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    payments = Payment.objects.select_related('order__customer', 'received_by').order_by('-payment_date')
    
    # Qidiruv
    search = request.GET.get('search')
    if search:
        payments = payments.filter(
            Q(order__order_number__icontains=search) |
            Q(order__customer__first_name__icontains=search) |
            Q(order__customer__last_name__icontains=search) |
            Q(order__customer__phone__icontains=search) |
            Q(receipt_number__icontains=search)
        )
    
    # To'lov turi filtri
    payment_type = request.GET.get('payment_type')
    if payment_type:
        payments = payments.filter(payment_type=payment_type)
    
    # To'lov usuli filtri
    payment_method = request.GET.get('payment_method')
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    # Sana filtri
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        payments = payments.filter(payment_date__date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__date__lte=date_to)
    
    # Tasdiqlash holati
    confirmed = request.GET.get('confirmed')
    if confirmed == 'yes':
        payments = payments.filter(is_confirmed=True)
    elif confirmed == 'no':
        payments = payments.filter(is_confirmed=False)
    
    # Statistika
    today = timezone.now().date()
    stats = {
        'total_payments': payments.count(),
        'total_amount': payments.aggregate(total=Sum('amount'))['total'] or 0,
        'today_payments': Payment.objects.filter(payment_date__date=today).count(),
        'today_amount': Payment.objects.filter(
            payment_date__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    payments = paginator.get_page(page_number)
    
    context = {
        'payments': payments,
        'search': search,
        'payment_type': payment_type,
        'payment_method': payment_method,
        'date_from': date_from,
        'date_to': date_to,
        'confirmed': confirmed,
        'stats': stats,
    }
    
    return render(request, 'payments/list.html', context)


@login_required
def payment_add(request, order_pk):
    """
    Buyurtmaga to'lov qo'shish
    """
    order = get_object_or_404(Order, pk=order_pk)
    
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda to\'lov qo\'shish huquqi yo\'q!')
        return redirect('orders:detail', pk=order_pk)
    
    # Bekor qilingan buyurtmalarga to'lov qo'shish mumkin emas
    if order.status == 'cancelled':
        messages.error(request, 'Bekor qilingan buyurtmalarga to\'lov qo\'shish mumkin emas!')
        return redirect('orders:detail', pk=order_pk)
    
    # To'liq to'langan buyurtmalarga to'lov qo'shish mumkin emas
    if order.is_fully_paid():
        messages.error(request, 'Bu buyurtma to\'liq to\'langan!')
        return redirect('orders:detail', pk=order_pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        form.order = order  # Form validation uchun
        
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.received_by = request.user
            
            # To'lov miqdorini tekshirish
            remaining = order.remaining_balance()
            if payment.amount > remaining:
                form.add_error('amount', f'To\'lov miqdori qolgan summadan ko\'p bo\'lmasligi kerak: {remaining:,} so\'m')
            else:
                payment.save()
                
                messages.success(
                    request, 
                    f'To\'lov qo\'shildi: {payment.amount:,} so\'m ({payment.get_payment_type_display()})'
                )
                return redirect('orders:detail', pk=order_pk)
    else:
        # Initial values
        remaining = order.remaining_balance()
        has_payments = order.payments.exists()
        
        # To'lov turini aniqlash
        if not has_payments:
            suggested_type = 'advance'
        elif remaining > 0:
            suggested_type = 'partial'
        else:
            suggested_type = 'final'
        
        form = PaymentForm(initial={
            'payment_type': suggested_type,
            'amount': remaining,
        })
        form.order = order  # Form validation uchun
    
    context = {
        'form': form,
        'order': order,
        'remaining_balance': order.remaining_balance(),
        'title': f'#{order.order_number} ga to\'lov qo\'shish',
    }
    
    return render(request, 'payments/form.html', context)


@login_required
def payment_edit(request, pk):
    """
    To'lovni tahrirlash
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    # Faqat admin tahrirlaya oladi
    if not request.user.is_admin():
        messages.error(request, 'Sizda to\'lovni tahrirlash huquqi yo\'q!')
        return redirect('orders:detail', pk=payment.order.pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        form.order = payment.order  # Form validation uchun
        
        if form.is_valid():
            payment = form.save()
            messages.success(request, 'To\'lov ma\'lumotlari yangilandi!')
            return redirect('orders:detail', pk=payment.order.pk)
    else:
        form = PaymentForm(instance=payment)
        form.order = payment.order  # Form validation uchun
    
    context = {
        'form': form,
        'payment': payment,
        'order': payment.order,
        'remaining_balance': payment.order.remaining_balance() + payment.amount,
        'title': f'To\'lovni tahrirlash',
    }
    
    return render(request, 'payments/form.html', context)


@login_required
def payment_delete(request, pk):
    """
    To'lovni o'chirish
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    # Faqat admin o'chira oladi
    if not request.user.is_admin():
        messages.error(request, 'Sizda to\'lovni o\'chirish huquqi yo\'q!')
        return redirect('orders:detail', pk=payment.order.pk)
    
    if request.method == 'POST':
        order_pk = payment.order.pk
        amount = payment.amount
        payment_type = payment.get_payment_type_display()
        reason = request.POST.get('reason', '')
        
        # History yaratish
        payment.order.create_history(
            action='payment_received',
            performed_by=request.user,
            notes=f'To\'lov o\'chirildi: {amount:,} so\'m ({payment_type}). Sabab: {reason}'
        )
        
        payment.delete()
        
        messages.success(
            request, 
            f'To\'lov o\'chirildi: {amount:,} so\'m ({payment_type})'
        )
        return redirect('orders:detail', pk=order_pk)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/delete.html', context)


@login_required
def daily_payment_report(request):
    """
    Kunlik to'lovlar hisoboti
    """
    # Faqat menejer va admin ko'ra oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    # Sana parametri
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Kun uchun to'lovlar
    payments = Payment.objects.filter(
        payment_date__date=selected_date,
        is_confirmed=True
    ).select_related('order__customer', 'received_by').order_by('-payment_date')
    
    # Statistika
    stats = {
        'total_payments': payments.count(),
        'total_amount': payments.aggregate(total=Sum('amount'))['total'] or 0,
        'advance_payments': payments.filter(payment_type='advance').aggregate(total=Sum('amount'))['total'] or 0,
        'partial_payments': payments.filter(payment_type='partial').aggregate(total=Sum('amount'))['total'] or 0,
        'final_payments': payments.filter(payment_type='final').aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # To'lov usullari bo'yicha statistika
    payment_methods = {}
    for method_code, method_name in Payment.PAYMENT_METHOD_CHOICES:
        amount = payments.filter(payment_method=method_code).aggregate(total=Sum('amount'))['total'] or 0
        if amount > 0:
            payment_methods[method_name] = amount
    
    context = {
        'payments': payments,
        'selected_date': selected_date,
        'stats': stats,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'payments/daily_report.html', context)