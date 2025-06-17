# orders/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.forms import inlineformset_factory

from .models import Order, OrderItem
from customers.models import Customer
from .forms import OrderForm, OrderItemForm
from django.utils import timezone


@login_required
def order_list(request):
    """
    Buyurtmalar ro'yxati
    """
    orders = Order.objects.select_related('customer', 'created_by').prefetch_related('items', 'payments')
    
    # Qidiruv
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer__first_name__icontains=search) |
            Q(customer__last_name__icontains=search) |
            Q(customer__phone__icontains=search)
        )
    
    # Status filtri
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # To'lov holati filtri
    payment_status = request.GET.get('payment_status')
    if payment_status == 'not_paid':
        orders = orders.order_by('-created_at')
        orders = [o for o in orders if o.total_paid() == 0]
    elif payment_status == 'partial':
        orders = orders.order_by('-created_at')
        orders = [o for o in orders if 0 < o.total_paid() < o.total_price()]
    elif payment_status == 'paid':
        orders = orders.order_by('-created_at')
        orders = [o for o in orders if o.is_fully_paid()]
    
    # Agar list bo'lmasa, querysetni order_by qilish
    if not isinstance(orders, list):
        orders = orders.order_by('-created_at')
    
    # Statistika
    all_orders = Order.objects.all()
    stats = {
        'new_orders': all_orders.filter(status='new').count(),
        'measuring_orders': all_orders.filter(status='measuring').count(),
        'processing_orders': all_orders.filter(status='processing').count(),
        'completed_orders': all_orders.filter(status='installed').count(),
        'cancelled_orders': all_orders.filter(status='cancelled').count(),
    }
    
    # Pagination (faqat queryset uchun)
    if not isinstance(orders, list):
        paginator = Paginator(orders, 20)
        page_number = request.GET.get('page')
        orders = paginator.get_page(page_number)
    
    context = {
        'orders': orders,
        'search': search,
        'status': status,
        'payment_status': payment_status,
        'stats': stats,
    }
    
    return render(request, 'orders/list.html', context)


@login_required
def order_detail(request, pk):
    """
    Buyurtma tafsilotlari
    """
    order = get_object_or_404(Order, pk=pk)
    
    # To'lovlar ro'yxati
    payments = order.payments.all().order_by('-payment_date')
    
    context = {
        'order': order,
        'payments': payments,
    }
    
    return render(request, 'orders/detail.html', context)


@login_required
def order_add(request):
    """
    Yangi buyurtma yaratish (soddalashtirilgan)
    """
    if not (request.user.is_manager() or request.user.is_admin() or request.user.can_create_order):
        messages.error(request, 'Sizda buyurtma yaratish huquqi yo\'q!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.status = 'measuring'  # Avtomatik o'lchovda holatiga o'tadi
            order.save()
            
            messages.success(
                request, 
                f'Buyurtma #{order.order_number} yaratildi! Status: O\'lchovda'
            )
            return redirect('orders:detail', pk=order.pk)
        else:
            # Form xatolarini ko'rsatish
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f'{field_label}: {error}')
    else:
        # URL dan mijozni olish
        customer_id = request.GET.get('customer')
        initial = {}
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
                initial['customer'] = customer
                initial['address'] = customer.address
            except Customer.DoesNotExist:
                pass
        
        form = OrderForm(initial=initial)
    
    context = {
        'form': form,
        'title': 'Yangi buyurtma yaratish',
        'simple_form': True,
    }
    
    return render(request, 'orders/simple_form.html', context)


@login_required
def order_measurement(request, pk):
    """
    O'lchov olish sahifasi
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Huquqlarni tekshirish
    if not (request.user.can_measure or request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda o\'lchov olish huquqi yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    # Faqat "measuring" statusdagi buyurtmalar uchun
    if order.status != 'measuring':
        messages.warning(request, 'Bu buyurtma o\'lchov olish bosqichida emas!')
        return redirect('orders:detail', pk=pk)
    
    # OrderItem formset yaratish
    OrderItemFormSet = inlineformset_factory(
        Order, OrderItem, 
        form=OrderItemForm,
        extra=1,
        min_num=1,
        validate_min=True,
        can_delete=True
    )
    
    if request.method == 'POST':
        formset = OrderItemFormSet(request.POST, instance=order)
        measurement_date = request.POST.get('measurement_date')
        measurement_notes = request.POST.get('measurement_notes')
        
        if formset.is_valid():
            # O'lchov ma'lumotlarini saqlash
            if measurement_date:
                from datetime import datetime
                order.measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
            
            if measurement_notes:
                if order.notes:
                    order.notes += f"\n\nO'lchov izohlar ({timezone.now().strftime('%d.%m.%Y')}): {measurement_notes}"
                else:
                    order.notes = f"O'lchov izohlar: {measurement_notes}"
            
            # Mas'ul xodimni belgilash
            order.measured_by = request.user
            order.status = 'processing'  # Ishlab chiqarishga o'tkazish
            order.save()
            
            # Jalyuzi ma'lumotlarini saqlash
            formset.save()
            
            messages.success(
                request, 
                f'O\'lchov muvaffaqiyatli yakunlandi! Buyurtma #{order.order_number} ishlab chiqarishga o\'tkazildi.'
            )
            return redirect('orders:detail', pk=order.pk)
        else:
            # Formset xatolarini ko'rsatish
            for form in formset:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Jalyuzi ma\'lumotlari: {error}')
            
            # Non-form errors
            for error in formset.non_form_errors():
                messages.error(request, f'Umumiy xato: {error}')
    else:
        formset = OrderItemFormSet(instance=order)
    
    context = {
        'order': order,
        'formset': formset,
        'today': timezone.now().date(),
        'title': f'O\'lchov olish - #{order.order_number}',
    }
    
    return render(request, 'orders/measurement.html', context)


@login_required
def order_edit(request, pk):
    """
    Buyurtmani tahrirlash
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda buyurtmani tahrirlash huquqi yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    # Tugallangan buyurtmalarni tahrirlash mumkin emas
    if order.status == 'installed':
        messages.error(request, 'Tugallangan buyurtmalarni tahrirlash mumkin emas!')
        return redirect('orders:detail', pk=pk)
    
    # OrderItem inline formset
    OrderItemFormSet = inlineformset_factory(
        Order, OrderItem,
        form=OrderItemForm,
        extra=0,
        can_delete=True,
        min_num=1,
        validate_min=True
    )
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order, prefix='form')
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.updated_by = request.user
            order.save()
            
            formset.save()
            
            messages.success(request, f'Buyurtma #{order.order_number} yangilandi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order, prefix='form')
    
    context = {
        'form': form,
        'formset': formset,
        'order': order,
        'title': f'Buyurtma #{order.order_number} tahrirlash',
    }
    
    return render(request, 'orders/edit.html', context)


@login_required
def order_delete(request, pk):
    """
    Buyurtmani o'chirish
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Faqat admin o'chira oladi
    if not request.user.is_admin():
        messages.error(request, 'Sizda buyurtmani o\'chirish huquqi yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    # To'lovlari bor buyurtmani o'chirish mumkin emas
    if order.payments.exists():
        messages.error(request, 'Bu buyurtmada to\'lovlar mavjud. Avval to\'lovlarni o\'chiring!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Buyurtma #{order_number} o\'chirildi!')
        return redirect('orders:list')
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/delete.html', context)


@login_required
def order_status_update(request, pk):
    """
    Buyurtma statusini yangilash
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin()):
        # Texnik xodim faqat o'z vazifalariga mos statuslarni o'zgartira oladi
        if not request.user.is_technician():
            messages.error(request, 'Sizda status o\'zgartirish huquqi yo\'q!')
            return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            old_status = order.get_status_display()
            order.status = new_status
            
            # Status bo'yicha mas'ul xodimlarni belgilash
            if new_status == 'measuring' and request.user.can_measure:
                order.measured_by = request.user
            elif new_status == 'processing' and request.user.can_process:
                order.processed_by = request.user
            elif new_status == 'installed' and request.user.can_install:
                order.installed_by = request.user
                order.installation_date = timezone.now().date()
            
            order.save()
            
            messages.success(
                request,
                f'Buyurtma #{order.order_number} statusi {old_status} dan {order.get_status_display()} ga o\'zgartirildi!'
            )
        else:
            messages.error(request, 'Noto\'g\'ri status tanlandi!')
    
    return redirect('orders:detail', pk=pk)


@login_required
def order_item_add(request, pk):
    """
    Buyurtmaga element qo'shish
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda element qo\'shish huquqi yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    # Tugallangan buyurtmalarga element qo'shish mumkin emas
    if order.status == 'installed':
        messages.error(request, 'Tugallangan buyurtmalarga element qo\'shish mumkin emas!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.order = order
            item.save()
            
            messages.success(request, 'Element buyurtmaga qo\'shildi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderItemForm()
    
    context = {
        'form': form,
        'order': order,
        'title': f'#{order.order_number} ga element qo\'shish',
    }
    
    return render(request, 'orders/add_item.html', context)


@login_required
def order_item_edit(request, pk):
    """
    Buyurtma elementini tahrirlash
    """
    item = get_object_or_404(OrderItem, pk=pk)
    order = item.order
    
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda element tahrirlash huquqi yo\'q!')
        return redirect('orders:detail', pk=order.pk)
    
    # Tugallangan buyurtmalar elementlarini tahrirlash mumkin emas
    if order.status == 'installed':
        messages.error(request, 'Tugallangan buyurtmalar elementlarini tahrirlash mumkin emas!')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        form = OrderItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Element ma\'lumotlari yangilandi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderItemForm(instance=item)
    
    context = {
        'form': form,
        'item': item,
        'order': order,
        'title': f'Element tahrirlash - #{order.order_number}',
    }
    
    return render(request, 'orders/edit_item.html', context)


@login_required
def order_item_delete(request, pk):
    """
    Buyurtma elementini o'chirish
    """
    item = get_object_or_404(OrderItem, pk=pk)
    order = item.order
    
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda element o\'chirish huquqi yo\'q!')
        return redirect('orders:detail', pk=order.pk)
    
    # Tugallangan buyurtmalar elementlarini o'chirish mumkin emas
    if order.status == 'installed':
        messages.error(request, 'Tugallangan buyurtmalar elementlarini o\'chirish mumkin emas!')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Element o\'chirildi!')
        return redirect('orders:detail', pk=order.pk)
    
    context = {
        'item': item,
        'order': order,
    }
    
    return render(request, 'orders/delete_item.html', context)


@login_required
def order_pdf(request, pk):
    """
    Buyurtmani PDF sifatida yuklab olish (print version)
    """
    order = get_object_or_404(Order, pk=pk)
    
    context = {
        'order': order,
    }
    
    # PDF uchun alohida template
    return render(request, 'orders/print.html', context)


@login_required
def order_ajax_stats(request):
    """
    AJAX orqali buyurtmalar statistikasi
    """
    # Umumiy statistika
    stats = {
        'total': Order.objects.count(),
        'new': Order.objects.filter(status='new').count(),
        'measuring': Order.objects.filter(status='measuring').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'installed': Order.objects.filter(status='installed').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    return JsonResponse(stats)