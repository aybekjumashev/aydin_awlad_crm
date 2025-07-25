# orders/views.py - TO'LIQ TUZATILGAN VERSIYA

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
from customers.models import Customer
from .forms import (
    SimpleOrderForm, 
    OrderUpdateForm, 
    OrderStatusUpdateForm,
    OrderItemForm, 
    OrderFilterForm, 
    AssignStaffForm,
    MeasurementFormSet
)
from payments.models import Payment
import json
from decimal import Decimal
import decimal
from datetime import date
from dateutil.relativedelta import relativedelta

@login_required
def order_list(request):
    """Buyurtmalar ro'yxati"""
    
    orders = Order.objects.select_related('customer').prefetch_related('items', 'payments')
    
    # Foydalanuvchi huquqiga qarab filtrlash
    if hasattr(request.user, 'is_technical') and request.user.is_technical and not getattr(request.user, 'can_view_all_orders', False):
        orders = orders.filter(
            Q(assigned_measurer=request.user) |
            Q(assigned_manufacturer=request.user) |
            Q(assigned_installer=request.user)
        )

        # Statistika ("new" status olib tashlandi)
    stats = {
        'total': orders.count(),
        'measuring': orders.filter(status='measuring').annotate(item_count=Count('items')).filter(item_count=0).count(),
        'not_comp_measuring': orders.filter(status='measuring').annotate(item_count=Count('items')).filter(item_count__gt=0).count(),
        'processing': orders.filter(status='processing').count(),
        'installing': orders.filter(status='installing').count(),
        'installed': orders.filter(status='installed').count(),
        'cancelled': orders.filter(status='cancelled').count(),
    }
    
    
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
            if status == 'not_comp_measuring':
                orders = orders.filter(status='measuring').annotate(item_count=Count('items')).filter(item_count__gt=0)
            elif status == 'measuring':
                orders = orders.filter(status='measuring').annotate(item_count=Count('items')).filter(item_count=0)
            else:
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
    

    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'stats': stats,
        'title': 'Buyurtmalar ro\'yxati'
    }
    
    return render(request, 'orders/list.html', context)


@login_required
def order_create(request):
    """Yangi buyurtma yaratish"""
    
    if request.method == 'POST':
        form = SimpleOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.save()
            
            messages.success(
                request, 
                f'Buyurtma #{order.order_number} muvaffaqiyatli yaratildi. '
                f'Endi o\'lchov olish jarayoniga o\'ting.'
            )
            return redirect('orders:detail', pk=order.pk)
    else:
        form = SimpleOrderForm()
        customer_id = request.GET.get('customer')
        customer = get_object_or_404(Customer, pk=customer_id)
    
    context = {
        'form': form,
        'title': 'Yangi buyurtma yaratish',
        'customer': customer
    }
    
    return render(request, 'orders/create.html', context)


@login_required
def order_detail(request, pk):
    """Buyurtma tafsilotlari"""
    
    order = get_object_or_404(Order, pk=pk)

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
        order.status = 'cancelled'
        order.cancelled_notes = request.POST.get('notes', '')
        order.save()
        messages.success(request, f'Buyurtma #{order_number} o\'chirildi!')

    return redirect('orders:list')
    

@login_required
def order_measurement(request, pk):
    """O'lchov olish va itemlarni saqlash - TUZATILGAN VERSIYA"""
    
    order = get_object_or_404(Order, pk=pk)
    
    # Ruxsat tekshirish
    if not (request.user.is_admin or request.user.is_manager or 
            (hasattr(request.user, 'can_measure') and request.user.can_measure)):
        messages.error(request, 'O\'lchov olish huquqingiz yo\'q!')
        return redirect('orders:detail', pk=order.pk)
    
    # Status tekshirish
    if order.status not in ['measuring', 'processing']:
        messages.error(request, 'Bu buyurtma uchun o\'lchov olish mumkin emas!')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        # O'lchov ma'lumotlarini saqlash
        measurement_notes = request.POST.get('measurement_notes', '')
        
        # Formset ma'lumotlarini olish
        formset = MeasurementFormSet(request.POST, instance=order)
        
        if formset.is_valid():
            # Eski itemlarni o'chirish
            order.items.all().delete()
            
            # Yangi itemlarni saqlash
            instances = formset.save(commit=False)
            total_amount = Decimal('0')
            
            for instance in instances:
                if instance.width and instance.height and instance.blind_type:
                    instance.order = order
                    instance.save()
                    total_amount += instance.total_price
            
            # Qo'shimcha itemlarni o'chirish (DELETE flag bilan)
            for obj in formset.deleted_objects:
                obj.delete()
            
            # Avans to'lov qo'shish
            advance_amount = request.POST.get('advance_payment')
            if advance_amount:
                try:
                    advance_amount = Decimal(str(advance_amount))
                    if advance_amount > 0:
                        Payment.objects.create(
                            order=order,
                            amount=advance_amount,
                            payment_method=request.POST.get('payment_method', 'cash'),
                            payment_type='prepayment',
                            payment_date=timezone.now(),
                            received_by=request.user,
                            notes='O\'lchov paytida qabul qilingan avans to\'lov',
                            status='confirmed'
                        )
                        order.paid_amount = advance_amount
                except (ValueError, TypeError, decimal.InvalidOperation):
                    messages.warning(request, 'Avans to\'lov miqdorida xatolik!')
            
            # Buyurtmani yangilash
            order.total_amount = total_amount
            order.measurement_notes = measurement_notes
            order.measurement_completed_date = timezone.now()
            
            # Faqat measuring holatida bo'lsa keyingi bosqichga o'tkazish
            if order.status == 'measuring':
                # print(request.POST.get('advance_payment_checkbox'))
                order.status = 'processing'
                order.assigned_measurer = request.user
            
            order.save()
            
            messages.success(
                request,
                'O\'lchov ma\'lumotlari saqlandi va buyurtma '
                'ishlab chiqarish bosqichiga o\'tkazildi'
            )
            return redirect('orders:detail', pk=order.pk)
        else:
            # Formset xatolarini ko'rsatish
            messages.error(request, 'Ma\'lumotlarda xatoliklar mavjud. Qaytadan tekshiring.')
    else:
        # GET so'rovi - formset yaratish
        formset = MeasurementFormSet(instance=order)
    
    # Context tayyorlash
    context = {
        'order': order,
        'formset': formset,
        'today': timezone.now().date(),
        'title': f'#{order.order_number} - O\'lchov olish'
    }
    
    return render(request, 'orders/measurement.html', context)


@login_required
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
def my_tasks(request):
    """Texnik xodim uchun mening vazifalarim"""
    
    if not hasattr(request.user, 'is_technical') or not request.user.is_technical:
        messages.error(request, 'Bu sahifa faqat texnik xodimlar uchun!')
        return redirect('dashboard')
    
    user = request.user
    
    # Mening barcha vazifalarim
    my_orders = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user)
    ).exclude(status__in=['installed', 'cancelled']).select_related('customer')
    
    # Filtrlash
    status_filter = request.GET.get('status', 'active')
    task_type = request.GET.get('task_type', 'all')
    
    if status_filter == 'completed':
        my_orders = Order.objects.filter(
            Q(assigned_measurer=user) |
            Q(assigned_manufacturer=user) |
            Q(assigned_installer=user),
            status='installed'
        ).select_related('customer')
    elif status_filter == 'overdue':
        # Kechikkan vazifalar - bu yerda mantiqni qo'shish mumkin
        pass
    
    # Vazifa turiga qarab filtrlash
    if task_type == 'measure' and user.can_measure:
        my_orders = my_orders.filter(assigned_measurer=user, status='measuring')
    elif task_type == 'manufacture' and user.can_manufacture:
        my_orders = my_orders.filter(assigned_manufacturer=user, status='processing')
    elif task_type == 'install' and user.can_install:
        my_orders = my_orders.filter(assigned_installer=user, status='installing')
    
    context = {
        'orders': my_orders,
        'status_filter': status_filter,
        'task_type': task_type,
        'title': 'Mening vazifalarim'
    }
    
    return render(request, 'technical/my_tasks.html', context)


def order_print(request, pk):
    """Buyurtmani chop etish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    context = {
        'order': order,
        'items': order.items.all(),
        'title': f'Buyurtma #{order.order_number} - Chop etish'
    }
    
    return render(request, 'orders/print.html', context)



@login_required
def generate_contract_view(request, order_id):
    """
    Buyurtma asosida shartnomani generatsiya qiladi va ko'rsatadi.
    """
    order = get_object_or_404(Order.objects.select_related('customer'), pk=order_id)
    customer = order.customer
    
    # Shartnoma uchun hisob-kitoblar
    total_price = order.total_price()
    
    # 1-variant: 50% oldindan to'lov
    prepayment_percentage = 50
    prepayment_amount = (total_price * Decimal(str(prepayment_percentage))) / 100
    
    # 2-variant: Qolgan summa va to'lov jadvali (masalan, 3 oyga bo'lib to'lash)
    remaining_amount = total_price - prepayment_amount
    months_for_payment = 3
    monthly_payment = remaining_amount / months_for_payment if months_for_payment > 0 else 0
    
    # ----- TO'G'RILASH BOSHLANDI -----
    # Qoldiq foizni view'da hisoblaymiz
    remaining_percentage = 100 - prepayment_percentage
    # ----- TO'G'RILASH TUGADI -----

    payment_schedule = []
    today = date.today()
    for i in range(1, months_for_payment + 1):
        payment_date = today + relativedelta(months=i)
        payment_schedule.append({
            'date': payment_date,
            'amount': monthly_payment
        })
        
    # Jami maydon (kv. metr)
    total_area_sqm = sum(item.area for item in order.items.all())
    
    context = {
        'order': order,
        'customer': customer,
        'total_price': total_price,
        'prepayment_percentage': prepayment_percentage,
        'prepayment_amount': prepayment_amount,
        'remaining_amount': remaining_amount,
        'payment_schedule': payment_schedule,
        'total_area_sqm': total_area_sqm,
        'today': today,
        'remaining_percentage': remaining_percentage, # YANGI: Tayyor natijani contextga qo'shamiz
    }
    
    return render(request, 'orders/contract.html', context)


@login_required
def order_add_payment(request, pk):
    """Buyurtmaga to'lov qo'shish"""
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'cash')
        notes = request.POST.get('notes', '')
        
        try:
            amount = Decimal(str(amount))  # ⭐ TUZATILDI: Decimal ishlatamiz
            if amount > 0:
                # To'lovni yaratish - TUZATILDI: payment_date qo'shildi
                payment = Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_method=payment_method,
                    payment_type='partial',
                    payment_date=timezone.now(),  # ⭐ Bu qator qo'shildi
                    received_by=request.user,     # ⭐ Qabul qilgan xodim ham qo'shildi
                    notes=notes,
                    status='confirmed'
                )
                
                # Order'dagi to'lov ma'lumotlarini yangilash
                order.paid_amount += payment.amount
                order.save()
                
                messages.success(request, f'{amount:,.0f} so\'m to\'lov qo\'shildi!')
            else:
                messages.error(request, 'To\'lov summasi 0 dan katta bo\'lishi kerak!')
        except (ValueError, decimal.InvalidOperation):  # ⭐ TUZATILDI: decimal xatoligini ham qo'shdik
            messages.error(request, 'Noto\'g\'ri summa kiritildi!')
    
    return redirect('orders:detail', pk=pk)


@login_required
def get_order_stats(request):
    """AJAX orqali buyurtma statistikalarini olish"""
    
    stats = {
        'total': Order.objects.count(),
        'measuring': Order.objects.filter(status='measuring').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'installing': Order.objects.filter(status='installing').count(),
        'installed': Order.objects.filter(status='installed').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    return JsonResponse(stats)