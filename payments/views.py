# payments/views.py - TUZATILGAN VERSIYA

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
# from .forms import PaymentForm  # Vaqtincha comment


@login_required
def payment_list(request):
    """
    To'lovlar ro'yxati - oddiy versiya
    """
    # TUZATILDI: () ni olib tashladim
    if not (getattr(request.user, 'is_manager', False) or getattr(request.user, 'is_admin', False)):
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
    # TUZATILDI: () ni olib tashladim
    if not (getattr(request.user, 'is_manager', False) or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sizda to\'lov qo\'shish huquqi yo\'q!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Form ma'lumotlarini olish
        order_id = request.POST.get('order_id')
        payment_type = request.POST.get('payment_type')
        payment_method = request.POST.get('payment_method')
        amount = request.POST.get('amount')
        payment_date = request.POST.get('payment_date')
        reference_number = request.POST.get('reference_number')
        notes = request.POST.get('notes')
        
        # Validatsiya
        try:
            order = Order.objects.get(pk=order_id) if order_id else None
            amount = float(amount) if amount else 0
            
            if not order:
                messages.error(request, 'Buyurtma tanlanishi kerak!')
            elif amount <= 0:
                messages.error(request, 'To\'lov summasi 0 dan katta bo\'lishi kerak!')
            else:
                # To'lov yaratish
                payment = Payment.objects.create(
                    order=order,
                    payment_type=payment_type,
                    payment_method=payment_method,
                    amount=amount,
                    payment_date=timezone.now() if not payment_date else payment_date,
                    reference_number=reference_number,
                    notes=notes,
                    received_by=request.user,
                    status='confirmed'  # Darhol tasdiqlash
                )
                
                # Buyurtma to'lov holatini yangilash
                order.paid_amount += payment.amount
                order.update_payment_status()
                order.save()
                
                messages.success(
                    request, 
                    f'To\'lov #{payment.id} muvaffaqiyatli qo\'shildi! '
                    f'Summa: {payment.amount:,.0f} so\'m'
                )
                return redirect('payments:detail', pk=payment.pk)
                
        except Order.DoesNotExist:
            messages.error(request, 'Buyurtma topilmadi!')
        except ValueError:
            messages.error(request, 'Summa noto\'g\'ri formatda!')
        except Exception as e:
            messages.error(request, f'Xatolik: {str(e)}')
    
    # Buyurtmalar ro'yxati
    orders = Order.objects.exclude(status='cancelled').select_related('customer').order_by('-created_at')[:50]
    
    # Payment type va method choices
    payment_type_choices = [
        ('prepayment', 'Oldindan to\'lov'),
        ('partial', 'Qisman to\'lov'),
        ('final', 'Yakuniy to\'lov'),
        ('full', 'To\'liq to\'lov'),
    ]
    
    payment_method_choices = [
        ('cash', 'Naqd pul'),
        ('card', 'Plastik karta'),
        ('transfer', 'Bank o\'tkazmasi'),
        ('mobile', 'Mobil to\'lov'),
    ]
    
    context = {
        'orders': orders,
        'payment_type_choices': payment_type_choices,
        'payment_method_choices': payment_method_choices,
        'title': 'Yangi to\'lov qo\'shish',
    }
    
    return render(request, 'payments/add_form.html', context)


@login_required
def payment_add_to_order(request, order_pk):
    """
    Buyurtmaga to'lov qo'shish
    """
    order = get_object_or_404(Order, pk=order_pk)
    
    # TUZATILDI: () ni olib tashladim
    if not (getattr(request.user, 'is_manager', False) or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sizda to\'lov qo\'shish huquqi yo\'q!')
        return redirect('orders:detail', pk=order_pk)
    
    # Vaqtincha sodda qilamiz
    messages.info(request, 'Buyurtmaga to\'lov qo\'shish funksiyasi rivojlantirilmoqda...')
    return redirect('orders:detail', pk=order_pk)


@login_required
def payment_detail(request, pk):
    """
    To'lov tafsilotlari
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    context = {
        'payment': payment,
        'title': f'To\'lov #{payment.id}'
    }
    
    return render(request, 'payments/detail.html', context)


@login_required
def payment_edit(request, pk):
    """
    To'lovni tahrirlash
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    # TUZATILDI: () ni olib tashladim
    if not (getattr(request.user, 'is_manager', False) or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sizda to\'lovni tahrirlash huquqi yo\'q!')
        return redirect('payments:detail', pk=pk)
    
    # Vaqtincha sodda qilamiz
    messages.info(request, 'To\'lovni tahrirlash funksiyasi rivojlantirilmoqda...')
    return redirect('payments:detail', pk=pk)


@login_required
def payment_delete(request, pk):
    """
    To'lovni o'chirish
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    # TUZATILDI: () ni olib tashladim
    if not (getattr(request.user, 'is_manager', False) or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sizda to\'lovni o\'chirish huquqi yo\'q!')
        return redirect('payments:detail', pk=pk)
    
    # Vaqtincha sodda qilamiz
    messages.info(request, 'To\'lovni o\'chirish funksiyasi rivojlantirilmoqda...')
    return redirect('payments:detail', pk=pk)


@login_required
def payment_confirm(request, pk):
    """
    To'lovni tasdiqlash
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    # TUZATILDI: () ni olib tashladim
    if not (getattr(request.user, 'is_manager', False) or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sizda to\'lovni tasdiqlash huquqi yo\'q!')
        return redirect('payments:detail', pk=pk)
    
    # Vaqtincha sodda qilamiz
    messages.info(request, 'To\'lovni tasdiqlash funksiyasi rivojlantirilmoqda...')
    return redirect('payments:detail', pk=pk)


@login_required
def payment_reports(request):
    """
    To'lovlar hisoboti
    """
    # TUZATILDI: () ni olib tashladim
    if not (getattr(request.user, 'is_manager', False) or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sizda hisobotlarni ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Q
    
    # Sana filtrlari
    today = datetime.now().date()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Default: oxirgi 30 kun
    if not date_from:
        date_from = today - timedelta(days=30)
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    
    if not date_to:
        date_to = today
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Asosiy to'lovlar filtri
    payments = Payment.objects.filter(
        payment_date__date__range=[date_from, date_to],
        status='confirmed'
    ).select_related('order', 'order__customer', 'received_by')
    
    # Umumiy statistika - TUZATILDI
    total_stats = payments.aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id')
    )
    
    # O'rtacha to'lovni alohida hisoblash
    if total_stats['total_count'] and total_stats['total_count'] > 0:
        total_stats['avg_payment'] = total_stats['total_amount'] / total_stats['total_count']
    else:
        total_stats['avg_payment'] = 0
    
    # To'lov usuli bo'yicha statistika
    method_stats = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # To'lov turi bo'yicha statistika
    type_stats = payments.values('payment_type').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # To'lov usuli bo'yicha statistika - display name bilan
    method_stats_with_display = []
    for method in method_stats:
        method_dict = dict(method)
        method_dict['display_name'] = method_display.get(method['payment_method'], method['payment_method'])
        method_stats_with_display.append(method_dict)
    
    # To'lov turi bo'yicha statistika - display name bilan
    type_stats_with_display = []
    for type_stat in type_stats:
        type_dict = dict(type_stat)
        type_dict['display_name'] = type_display.get(type_stat['payment_type'], type_stat['payment_type'])
        type_stats_with_display.append(type_dict)
    
    # Xodimlar bo'yicha statistika
    staff_stats = payments.values(
        'received_by__first_name', 'received_by__last_name', 'received_by__username'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Kunlik dinamika (oxirgi 7 kun)
    daily_stats = []
    for i in range(7):
        day = today - timedelta(days=i)
        day_payments = payments.filter(payment_date__date=day)
        daily_total = day_payments.aggregate(total=Sum('amount'))['total'] or 0
        daily_count = day_payments.count()
        
        daily_stats.append({
            'date': day,
            'total': daily_total,
            'count': daily_count
        })
    
    daily_stats.reverse()  # Eskidan yangiliga
    
    # Eng katta to'lovlar
    top_payments = payments.order_by('-amount')[:10]
    
    # Payment method choices for display - TUZATILDI
    try:
        method_display = dict(Payment.PAYMENT_METHOD_CHOICES)
        type_display = dict(Payment.PAYMENT_TYPE_CHOICES)
    except:
        # Agar Payment model'da choices mavjud bo'lmasa
        method_display = {
            'cash': 'Naqd pul',
            'card': 'Plastik karta', 
            'transfer': 'Bank o\'tkazmasi',
            'mobile': 'Mobil to\'lov',
            'online': 'Online to\'lov',
            'installment': 'Muddatli to\'lov',
        }
        type_display = {
            'prepayment': 'Oldindan to\'lov',
            'partial': 'Qisman to\'lov',
            'final': 'Yakuniy to\'lov',
            'full': 'To\'liq to\'lov',
            'refund': 'Qaytarilgan to\'lov',
            'discount': 'Chegirma',
        }
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_stats': total_stats,
        'method_stats': method_stats_with_display,
        'type_stats': type_stats_with_display,
        'staff_stats': staff_stats,
        'daily_stats': daily_stats,
        'top_payments': top_payments,
        'payments_count': payments.count(),
        'title': 'To\'lovlar hisoboti'
    }
    
    return render(request, 'payments/reports.html', context)


@login_required
def daily_payment_report(request):
    """
    Kunlik to'lovlar hisoboti
    """
    # TUZATILDI: () ni olib tashladim
    if not (getattr(request.user, 'is_manager', False) or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count
    
    # Bugungi sana
    target_date = request.GET.get('date')
    if target_date:
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    else:
        target_date = datetime.now().date()
    
    # Bugungi to'lovlar
    daily_payments = Payment.objects.filter(
        payment_date__date=target_date,
        status='confirmed'
    ).select_related('order', 'order__customer', 'received_by').order_by('-payment_date')
    
    # Bugungi statistika
    daily_stats = daily_payments.aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id')
    )
    
    # To'lov usuli bo'yicha bugungi statistika
    method_breakdown = daily_payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Xodimlar bo'yicha bugungi statistika
    staff_breakdown = daily_payments.values(
        'received_by__first_name', 'received_by__last_name'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Soatlik taqsimlash
    hourly_stats = []
    for hour in range(24):
        hour_payments = daily_payments.filter(payment_date__hour=hour)
        hour_total = hour_payments.aggregate(total=Sum('amount'))['total'] or 0
        hour_count = hour_payments.count()
        
        if hour_total > 0:  # Faqat to'lov bo'lgan soatlarni ko'rsatish
            hourly_stats.append({
                'hour': f"{hour:02d}:00",
                'total': hour_total,
                'count': hour_count
            })
    
    # Oxirgi 7 kunlik taqqoslash
    week_comparison = []
    for i in range(7):
        day = target_date - timedelta(days=i)
        day_payments = Payment.objects.filter(
            payment_date__date=day,
            status='confirmed'
        )
        day_total = day_payments.aggregate(total=Sum('amount'))['total'] or 0
        day_count = day_payments.count()
        
        week_comparison.append({
            'date': day,
            'total': day_total,
            'count': day_count,
            'is_today': day == target_date
        })
    
    week_comparison.reverse()
    
    # Payment method display
    method_display = dict(Payment.PAYMENT_METHOD_CHOICES)
    
    context = {
        'target_date': target_date,
        'daily_payments': daily_payments,
        'daily_stats': daily_stats,
        'method_breakdown': method_breakdown,
        'staff_breakdown': staff_breakdown,
        'hourly_stats': hourly_stats,
        'week_comparison': week_comparison,
        'method_display': method_display,
        'title': f'{target_date.strftime("%d.%m.%Y")} - Kunlik hisobot'
    }
    
    return render(request, 'payments/daily_report.html', context)


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
            'total_amount': float(order.total_amount),
            'paid_amount': float(order.paid_amount),
            'remaining': float(order.remaining_amount),
            'status': order.get_status_display(),
        }
        
        return JsonResponse(data)
    
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Buyurtma topilmadi'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)