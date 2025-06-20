# orders/views.py - IMPORT TUZATILGAN VERSIYA

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
# Import'larni tuzatamiz - faqat mavjud form'lar
from .forms import (
    SimpleOrderForm, 
    OrderUpdateForm, 
    OrderStatusUpdateForm,  # OrderStatusForm o'rniga
    OrderItemForm, 
    OrderFilterForm, 
    AssignStaffForm,
    MeasurementFormSet
)
from payments.models import Payment
# from payments.forms import QuickPaymentForm  # Vaqtincha comment
# from accounts.decorators import role_required, can_create_order, can_manage_payments  # Vaqtincha comment
import json


@login_required
def order_list(request):
    """Buyurtmalar ro'yxati"""
    
    orders = Order.objects.select_related('customer').prefetch_related('items', 'payments')
    
    # Foydalanuvchi huquqiga qarab filtrlash
    if hasattr(request.user, 'is_technical') and request.user.is_technical and not getattr(request.user, 'can_view_all_orders', False):
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
# @can_create_order  # Vaqtincha comment
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
    
    return render(request, 'orders/create.html', context)


@login_required
def order_detail(request, pk):
    """Buyurtma tafsilotlari"""
    
    order = get_object_or_404(Order, pk=pk)
    
    # Texnik xodim faqat o'ziga tayinlangan buyurtmalarni ko'ra oladi
    if (hasattr(request.user, 'is_technical') and 
        request.user.is_technical and 
        not getattr(request.user, 'can_view_all_orders', False)):
        
        if not (order.assigned_measurer == request.user or 
                order.assigned_manufacturer == request.user or 
                order.assigned_installer == request.user):
            messages.error(request, 'Bu buyurtmani ko\'rish huquqingiz yo\'q!')
            return redirect('orders:list')
    
    # Buyurtma elementlari
    items = order.items.all()
    
    # To'lovlar
    payments = order.payments.all().order_by('-payment_date')
    
    context = {
        'order': order,
        'items': items,
        'payments': payments,
        'title': f'Buyurtma #{order.order_number}'
    }
    
    return render(request, 'orders/detail.html', context)


@login_required
def order_edit(request, pk):
    """Buyurtmani tahrirlash"""
    
    order = get_object_or_404(Order, pk=pk)
    
    # Faqat admin va menejer tahrirlashi mumkin
    if not (getattr(request.user, 'is_admin', False) or getattr(request.user, 'is_manager', False)):
        messages.error(request, 'Buyurtmani tahrirlash huquqingiz yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        form = OrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Buyurtma muvaffaqiyatli yangilandi!')
            return redirect('orders:detail', pk=pk)
    else:
        form = OrderUpdateForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
        'title': f'#{order.order_number} - Tahrirlash'
    }
    
    return render(request, 'orders/edit.html', context)


@login_required
def order_delete(request, pk):
    """Buyurtmani o'chirish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    # Faqat admin o'chira oladi
    if not getattr(request.user, 'is_admin', False):
        messages.error(request, 'Buyurtmani o\'chirish huquqingiz yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Buyurtma #{order_number} o\'chirildi!')
        return redirect('orders:list')
    
    context = {
        'order': order,
        'title': f'#{order.order_number} - O\'chirish'
    }
    
    return render(request, 'orders/delete.html', context)


@login_required
def order_measurement(request, pk):
    """O'lchov olish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    # Huquqlarni tekshirish
    if not (getattr(request.user, 'can_measure', False) or 
            getattr(request.user, 'is_manager', False) or 
            getattr(request.user, 'is_admin', False)):
        messages.error(request, 'O\'lchov olish huquqingiz yo\'q!')
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
# @role_required(['admin', 'manager'])  # Vaqtincha comment
def order_status_update(request, pk):
    """Buyurtma statusini o'zgartirish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderStatusUpdateForm(request.POST, instance=order, user=request.user)
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
        form = OrderStatusUpdateForm(instance=order, user=request.user)
    
    context = {
        'form': form,
        'order': order,
        'title': f'#{order.order_number} - Status o\'zgartirish'
    }
    
    return render(request, 'orders/status_update.html', context)


@login_required
def order_assign_staff(request, pk):
    """Xodimlarni tayinlash"""
    
    order = get_object_or_404(Order, pk=pk)
    
    # Faqat admin va menejer tayinlashi mumkin
    if not (getattr(request.user, 'is_admin', False) or getattr(request.user, 'is_manager', False)):
        messages.error(request, 'Xodim tayinlash huquqingiz yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        form = AssignStaffForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Xodimlar muvaffaqiyatli tayinlandi!')
            return redirect('orders:detail', pk=pk)
    else:
        form = AssignStaffForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
        'title': f'#{order.order_number} - Xodim tayinlash'
    }
    
    return render(request, 'orders/assign_staff.html', context)


@login_required
def order_print(request, pk):
    """Buyurtma chop etish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    context = {
        'order': order,
        'items': order.items.all(),
        'payments': order.payments.all(),
    }
    
    return render(request, 'orders/print.html', context)


@login_required
def order_add_payment(request, pk):
    """Buyurtmaga to'lov qo'shish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    # Bu funksionalni vaqtincha sodda qilamiz
    messages.info(request, 'To\'lov qo\'shish funksiyasi rivojlantirilmoqda...')
    return redirect('orders:detail', pk=pk)


@login_required
def get_order_stats(request):
    """API: Buyurtma statistikalari"""
    
    stats = {
        'total': Order.objects.count(),
        'new': Order.objects.filter(status='new').count(),
        'measuring': Order.objects.filter(status='measuring').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'installing': Order.objects.filter(status='installing').count(),
        'installed': Order.objects.filter(status='installed').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    return JsonResponse(stats)


@login_required
def my_tasks(request):
    """Mening vazifalarim (texnik xodim uchun)"""
    
    if not getattr(request.user, 'is_technical', False):
        messages.error(request, 'Bu sahifa faqat texnik xodimlar uchun!')
        return redirect('dashboard')
    
    user = request.user
    
    # Mening buyurtmalarim
    orders = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user)
    ).select_related('customer').order_by('-created_at')
    
    context = {
        'orders': orders,
        'user': user,
        'title': 'Mening vazifalarim'
    }
    
    return render(request, 'orders/my_tasks.html', context)