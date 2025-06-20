# payments/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
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
    To'lovlar ro'yxati - oddiy versiya
    """
    # Faqat menejer va admin ko'ra oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    payments = Payment.objects.select_related('order', 'order__customer').order_by('-payment_date')[:50]
    
    context = {
        'payments': payments,
        'title': 'To\'lovlar ro\'yxati'
    }
    
    return render(request, 'payments/list.html', context)


@login_required
def payment_add(request):
    """
    Yangi to'lov qo'shish (buyurtmasiz)
    """
    # Faqat menejer va admin qo'sha oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda to\'lov qo\'shish huquqi yo\'q!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.received_by = request.user
            payment.save()
            
            messages.success(request, f'To\'lov #{payment.id} qo\'shildi!')
            return redirect('payments:detail', pk=payment.pk)
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'title': 'Yangi to\'lov qo\'shish',
    }
    
    return render(request, 'payments/form.html', context)


@login_required
def payment_add_to_order(request, order_pk):
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
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.received_by = request.user
            payment.save()
            
            messages.success(request, f'To\'lov {payment.amount:,.0f} so\'m buyurtmaga qo\'shildi!')
            return redirect('orders:detail', pk=order_pk)
    else:
        # Buyurtma ma'lumotlari bilan form ni to'ldirish
        initial = {
            'order': order,
            'payment_type': 'partial',  # Default qisman to'lov
        }
        form = PaymentForm(initial=initial)
    
    context = {
        'form': form,
        'order': order,
        'title': f'Buyurtma #{order.order_number}ga to\'lov qo\'shish',
    }
    
    return render(request, 'payments/form.html', context)


@login_required
def payment_detail(request, pk):
    """
    To'lov tafsilotlari
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    context = {
        'payment': payment,
        'order': payment.order,
    }
    
    return render(request, 'payments/detail.html', context)


@login_required
def payment_edit(request, pk):
    """
    To'lovni tahrirlash
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    # Faqat menejer va admin tahrirlaya oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda to\'lovni tahrirlash huquqi yo\'q!')
        return redirect('payments:detail', pk=pk)
    
    # Tasdiqlangan to'lovlarni tahrirlash mumkin emas
    if payment.is_confirmed:
        messages.error(request, 'Tasdiqlangan to\'lovlarni tahrirlash mumkin emas!')
        return redirect('payments:detail', pk=pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'To\'lov ma\'lumotlari yangilandi!')
            return redirect('payments:detail', pk=pk)
    else:
        form = PaymentForm(instance=payment)
    
    context = {
        'form': form,
        'payment': payment,
        'title': f'To\'lov #{payment.id} tahrirlash',
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
        return redirect('payments:detail', pk=pk)
    
    # Tasdiqlangan to'lovlarni o'chirish mumkin emas
    if payment.is_confirmed:
        messages.error(request, 'Tasdiqlangan to\'lovlarni o\'chirish mumkin emas!')
        return redirect('payments:detail', pk=pk)
    
    if request.method == 'POST':
        order_pk = payment.order.pk if payment.order else None
        payment.delete()
        messages.success(request, 'To\'lov o\'chirildi!')
        
        if order_pk:
            return redirect('orders:detail', pk=order_pk)
        else:
            return redirect('payments:list')
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/delete.html', context)

@login_required
def payment_confirm(request, pk):
    """
    To'lovni tasdiqlash
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    # Faqat menejer va admin tasdiqlaya oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda to\'lovni tasdiqlash huquqi yo\'q!')
        return redirect('payments:detail', pk=pk)
    
    if not payment.is_confirmed:
        payment.is_confirmed = True
        payment.confirmed_by = request.user
        payment.confirmed_at = timezone.now()
        payment.save()
        
        messages.success(request, f'To\'lov #{payment.id} tasdiqlandi!')
    else:
        messages.info(request, 'To\'lov allaqachon tasdiqlangan!')
    
    return redirect('payments:detail', pk=pk)
@login_required
def payment_reports(request):
    """
    To'lovlar hisoboti (payments app ichida)
    """
    # Bu funksiya reports.views.payment_report ga redirect qiladi
    return redirect('reports:payments')

@login_required
def payment_ajax_order_info(request):
    """
    AJAX orqali buyurtma ma'lumotlari
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Faqat AJAX so\'rovlar'}, status=400)
    
    order_id = request.GET.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'Buyurtma ID kiritilmagan'}, status=400)
    
    try:
        order = Order.objects.get(pk=order_id)
        
        data = {
            'order_number': order.order_number,
            'customer_name': order.customer.get_full_name(),
            'total_price': float(order.total_price()),
            'total_paid': float(order.total_paid()),
            'remaining': float(order.remaining_balance()),
            'status': order.get_status_display(),
        }
        
        return JsonResponse(data)
    
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Buyurtma topilmadi'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




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
            from datetime import datetime
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

