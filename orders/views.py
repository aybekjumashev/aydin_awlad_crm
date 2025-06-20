# orders/views.py - TUZATILGAN VERSIYA

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.forms import modelformset_factory

from .models import Order, OrderItem
from .forms import (
    SimpleOrderForm, OrderUpdateForm, OrderStatusForm, 
    OrderItemForm, OrderFilterForm, AssignStaffForm,
    MeasurementFormSet
)
from payments.models import Payment
from payments.forms import QuickPaymentForm
from accounts.decorators import role_required, can_create_order, can_manage_payments
import json


@login_required
def order_list(request):
    """Buyurtmalar ro'yxati"""
    
    orders = Order.objects.select_related('customer').prefetch_related('items', 'payments')
    
    # Foydalanuvchi huquqiga qarab filtrlash
    if request.user.is_technical and not request.user.can_view_all_orders:
        # Texnik xodim faqat o'ziga tayinlangan buyurtmalarni ko'radi
        orders = orders.filter(
            Q(assigned_measurer=request.user) |
            Q(assigned_manufacturer=request.user) |
            Q(assigned_installer=request.user)
        )
    
    # Filtrlash
    filter_form = OrderFilterForm(request.GET)
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        status = filter_form.cleaned_data.get('status')
        customer = filter_form.cleaned_data.get('customer')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        assigned_to = filter_form.cleaned_data.get('assigned_to')
        
        if search:
            orders = orders.filter(
                Q(order_number__icontains=search) |
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__phone__icontains=search)
            )
        
        if status:
            orders = orders.filter(status=status)
        
        if customer:
            orders = orders.filter(customer=customer)
        
        if date_from:
            orders = orders.filter(created_at__date__gte=date_from)
        
        if date_to:
            orders = orders.filter(created_at__date__lte=date_to)
        
        if assigned_to:
            orders = orders.filter(
                Q(assigned_measurer=assigned_to) |
                Q(assigned_manufacturer=assigned_to) |
                Q(assigned_installer=assigned_to)
            )
    
    # Sahifalash
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistika
    stats = {
        'total': orders.count(),
        'new': orders.filter(status='new').count(),
        'measuring': orders.filter(status='measuring').count(),
        'processing': orders.filter(status='processing').count(),
        'installing': orders.filter(status='installing').count(),
        'installed': orders.filter(status='installed').count(),
        'cancelled': orders.filter(status='cancelled').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'stats': stats,
        'title': 'Buyurtmalar ro\'yxati'
    }
    
    return render(request, 'orders/list.html', context)


@login_required
@can_create_order
def order_create(request):
    """Yangi buyurtma yaratish - Oddiy forma"""
    
    if request.method == 'POST':
        form = SimpleOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            # Status avtomatik "measuring" ga o'rnatiladi modelda
            order.save()
            
            messages.success(
                request, 
                f'Buyurtma #{order.order_number} muvaffaqiyatli yaratildi. '
                f'Endi o\'lchov olish jarayoniga o\'ting.'
            )
            return redirect('orders:detail', pk=order.pk)
    else:
        form = SimpleOrderForm()
    
    context = {
        'form': form,
        'title': 'Yangi buyurtma yaratish'
    }
    
    return render(request, 'orders/simple_form.html', context)


@login_required
def order_detail(request, pk):
    """Buyurtma tafsiloti"""
    
    order = get_object_or_404(Order, pk=pk)
    
    # Huquqlarni tekshirish
    if (request.user.is_technical and 
        not request.user.can_view_all_orders and
        order.assigned_measurer != request.user and
        order.assigned_manufacturer != request.user and
        order.assigned_installer != request.user):
        messages.error(request, 'Bu buyurtmani ko\'rish huquqingiz yo\'q')
        return redirect('orders:list')
    
    items = order.items.all()
    payments = order.payments.filter(status='confirmed').order_by('-payment_date')
    
    # Tezkor to'lov formasi
    quick_payment_form = QuickPaymentForm(order=order)
    
    context = {
        'order': order,
        'items': items,
        'payments': payments,
        'quick_payment_form': quick_payment_form,
        'title': f'Buyurtma #{order.order_number}'
    }
    
    return render(request, 'orders/detail.html', context)


@login_required
@role_required(['admin', 'manager'])
def order_edit(request, pk):
    """Buyurtmani tahrirlash"""
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Buyurtma muvaffaqiyatli yangilandi')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderUpdateForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
        'title': f'#{order.order_number} - Tahrirlash'
    }
    
    return render(request, 'orders/edit.html', context)


@login_required
def order_measurement(request, pk):
    """O'lchov olish va jalyuzilar qo'shish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    # Huquqlarni tekshirish
    if (not request.user.can_measure and 
        not request.user.is_manager and 
        not request.user.is_admin):
        messages.error(request, 'O\'lchov olish huquqingiz yo\'q')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        formset = MeasurementFormSet(request.POST, instance=order)
        
        if formset.is_valid():
            formset.save()
            
            # O'lchov yakunlangan sanani belgilash
            order.measurement_completed_date = timezone.now()
            if order.status == 'measuring':
                order.status = 'processing'  # Keyingi bosqichga o'tkazish
            order.save()
            
            messages.success(
                request,
                'O\'lchov ma\'lumotlari saqlandi va buyurtma '
                'ishlab chiqarish bosqichiga o\'tkazildi'
            )
            return redirect('orders:detail', pk=order.pk)
    else:
        formset = MeasurementFormSet(instance=order)
    
    context = {
        'order': order,
        'formset': formset,
        'title': f'#{order.order_number} - O\'lchov olish'
    }
    
    return render(request, 'orders/measurement.html', context)


@login_required
@role_required(['admin', 'manager'])
def order_status_update(request, pk):
    """Buyurtma statusini o'zgartirish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order, user=request.user)
        if form.is_valid():
            old_status = order.status
            new_status = form.cleaned_data['status']
            
            # Status o'zgarganda tegishli sanalarni belgilash
            if new_status == 'processing' and old_status != 'processing':
                order.production_start_date = timezone.now()
            elif new_status == 'installing' and old_status != 'installing':
                order.production_completed_date = timezone.now()
            elif new_status == 'installed' and old_status != 'installed':
                order.installation_completed_date = timezone.now()
            
            form.save()
            
            messages.success(
                request,
                f'Buyurtma holati "{order.get_status_display()}" ga o\'zgartirildi'
            )
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderStatusForm(instance=order, user=request.user)
    
    context = {
        'form': form,
        'order': order,
        'title': f'#{order.order_number} - Status o\'zgartirish'
    }
    
    return render(request, 'orders/status_update.html', context)


@login_required
@role_required(['admin', 'manager'])
def order_assign_staff(request, pk):
    """Xodimlarni tayinlash"""
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = AssignStaffForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Xodimlar muvaffaqiyatli tayinlandi')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = AssignStaffForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
        'title': f'#{order.order_number} - Xodim tayinlash'
    }
    
    return render(request, 'orders/assign_staff.html', context)


@login_required
@can_manage_payments
@require_POST
def order_add_payment(request, pk):
    """Tezkor to'lov qo'shish (AJAX)"""
    
    order = get_object_or_404(Order, pk=pk)
    
    form = QuickPaymentForm(request.POST, order=order)
    if form.is_valid():
        # To'lovni yaratish
        payment = Payment.objects.create(
            order=order,
            payment_type='partial',  # Tezkor to'lov uchun
            payment_method=form.cleaned_data['payment_method'],
            amount=form.cleaned_data['amount'],
            payment_date=timezone.now(),
            status='confirmed',
            received_by=request.user,
            confirmed_by=request.user,
            notes=form.cleaned_data.get('notes', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{payment.amount:,.0f} so\'m to\'lov qo\'shildi',
            'payment_id': payment.id,
            'new_paid_amount': f'{order.paid_amount:,.0f}',
            'new_remaining': f'{order.remaining_amount:,.0f}',
            'payment_status': order.get_payment_status_display()
        })
    else:
        errors = []
        for field, field_errors in form.errors.items():
            for error in field_errors:
                errors.append(f'{form.fields[field].label}: {error}')
        
        return JsonResponse({
            'error': 'Forma xatolari: ' + '; '.join(errors)
        }, status=400)


@login_required
def order_print(request, pk):
    """Buyurtmani chop etish uchun sahifa"""
    
    order = get_object_or_404(Order, pk=pk)
    items = order.items.all()
    payments = order.payments.filter(status='confirmed')
    
    context = {
        'order': order,
        'items': items,
        'payments': payments,
        'print_date': timezone.now()
    }
    
    return render(request, 'orders/print.html', context)


@login_required
@role_required(['admin', 'manager'])
def order_delete(request, pk):
    """Buyurtmani o'chirish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    if order.status in ['processing', 'installing', 'installed']:
        messages.error(
            request, 
            'Ishlanayotgan yoki yakunlangan buyurtmani o\'chirish mumkin emas'
        )
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Buyurtma #{order_number} o\'chirildi')
        return redirect('orders:list')
    
    context = {
        'order': order,
        'title': f'#{order.order_number} - O\'chirish'
    }
    
    return render(request, 'orders/delete_confirm.html', context)


# AJAX Views

@login_required
def get_order_stats(request):
    """Buyurtmalar statistikasi (AJAX uchun)"""
    
    orders = Order.objects.all()
    
    # Foydalanuvchi huquqiga qarab filtrlash
    if request.user.is_technical and not request.user.can_view_all_orders:
        orders = orders.filter(
            Q(assigned_measurer=request.user) |
            Q(assigned_manufacturer=request.user) |
            Q(assigned_installer=request.user)
        )
    
    stats = {
        'total': orders.count(),
        'by_status': {
            'new': orders.filter(status='new').count(),
            'measuring': orders.filter(status='measuring').count(),
            'processing': orders.filter(status='processing').count(),
            'installing': orders.filter(status='installing').count(),
            'installed': orders.filter(status='installed').count(),
            'cancelled': orders.filter(status='cancelled').count(),
        },
        'by_payment': {
            'pending': orders.filter(payment_status='pending').count(),
            'partial': orders.filter(payment_status='partial').count(),
            'paid': orders.filter(payment_status='paid').count(),
        },
        'total_revenue': orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
        'total_paid': orders.aggregate(
            total=Sum('paid_amount')
        )['total'] or 0,
    }
    
    return JsonResponse(stats)


@login_required
def my_tasks(request):
    """Texnik xodim uchun o'zining vazifalari"""
    
    if not request.user.is_technical:
        messages.error(request, 'Bu sahifa faqat texnik xodimlar uchun')
        return redirect('dashboard')
    
    tasks = []
    
    # O'lchov olish vazifalari
    if request.user.can_measure:
        measuring_orders = Order.objects.filter(
            assigned_measurer=request.user,
            status='measuring'
        ).select_related('customer')
        
        for order in measuring_orders:
            tasks.append({
                'order': order,
                'task_type': 'measure',
                'task_name': 'O\'lchov olish',
                'priority': 'high' if not order.measurement_date else 'normal',
                'due_date': order.measurement_date
            })
    
    # Ishlab chiqarish vazifalari
    if request.user.can_manufacture:
        processing_orders = Order.objects.filter(
            assigned_manufacturer=request.user,
            status='processing'
        ).select_related('customer')
        
        for order in processing_orders:
            tasks.append({
                'order': order,
                'task_type': 'manufacture',
                'task_name': 'Ishlab chiqarish',
                'priority': 'normal',
                'due_date': order.production_start_date
            })
    
    # O'rnatish vazifalari
    if request.user.can_install:
        installing_orders = Order.objects.filter(
            assigned_installer=request.user,
            status='installing'
        ).select_related('customer')
        
        for order in installing_orders:
            tasks.append({
                'order': order,
                'task_type': 'install',
                'task_name': 'O\'rnatish',
                'priority': 'high',
                'due_date': order.installation_date
            })
    
    # Vazifalarni sanaga qarab saralash
    tasks.sort(key=lambda x: x['due_date'] or timezone.now())
    
    context = {
        'tasks': tasks,
        'title': 'Mening vazifalarim'
    }
    
    return render(request, 'orders/my_tasks.html', context)