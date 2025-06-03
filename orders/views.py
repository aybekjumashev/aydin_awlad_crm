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
        # Bu yerda queryset ni list ga aylantirishdan oldin order_by qilish kerak
        orders = orders.order_by('-created_at')
        orders = [o for o in orders if o.total_paid() == 0]
    elif payment_status == 'partial':
        orders = orders.order_by('-created_at')
        orders = [o for o in orders if 0 < o.total_paid() < o.total_price()]
    elif payment_status == 'paid':
        orders = orders.order_by('-created_at')
        orders = [o for o in orders if o.is_fully_paid()]
    
    # Texnik xodim uchun faqat o'ziga tegishli buyurtmalar
    if request.user.is_technician():
        orders = orders.filter(
            Q(measured_by=request.user) |
            Q(processed_by=request.user) |
            Q(installed_by=request.user) |
            Q(created_by=request.user)
        ).distinct()
    
    # Statistika
    all_orders = Order.objects.all()
    stats = {
        'new_orders': all_orders.filter(status='new').count(),
        'measuring_orders': all_orders.filter(status='measuring').count(),
        'processing_orders': all_orders.filter(status='processing').count(),
        'completed_orders': all_orders.filter(status='installed').count(),
        'cancelled_orders': all_orders.filter(status='cancelled').count(),
    }
    
    # Pagination
    orders_is_list = isinstance(orders, list)
    
    if orders_is_list:  # Agar filter natijasida list bo'lsa
        paginator = Paginator(orders, 20)
        page_number = request.GET.get('page')
        orders = paginator.get_page(page_number)
    else:
        # Agar payment filter qo'llanilmagan bo'lsa, oddiy queryset
        orders = orders.order_by('-created_at')
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
    order = get_object_or_404(
        Order.objects.select_related('customer', 'created_by', 'measured_by', 'processed_by', 'installed_by')
        .prefetch_related('items', 'payments__received_by', 'history__performed_by'),
        pk=pk
    )
    
    # Texnik xodim faqat o'ziga tegishli buyurtmalarni ko'ra oladi
    if request.user.is_technician():
        if not (order.measured_by == request.user or 
                order.processed_by == request.user or 
                order.installed_by == request.user or 
                order.created_by == request.user):
            messages.error(request, 'Sizda bu buyurtmani ko\'rish huquqi yo\'q!')
            return redirect('orders:list')
    
    context = {
        'order': order,
        'items': order.items.all(),
        'payments': order.payments.all().order_by('-payment_date'),
        'history': order.history.all().order_by('-created_at')[:10],
    }
    
    return render(request, 'orders/detail.html', context)


@login_required
def order_add(request):
    """
    Yangi buyurtma yaratish
    """
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin() or request.user.can_create_order):
        messages.error(request, 'Sizda buyurtma yaratish huquqi yo\'q!')
        return redirect('orders:list')
    
    # OrderItem inline formset
    OrderItemFormSet = inlineformset_factory(
        Order, OrderItem, 
        form=OrderItemForm,
        extra=1, 
        can_delete=True,
        min_num=1,
        validate_min=True
    )
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.updated_by = request.user
            order.save()
            
            formset.instance = order
            formset.save()
            
            # History yaratish
            order.create_history(
                action='created',
                performed_by=request.user,
                notes=f'Buyurtma yaratildi. Jami {order.total_items()} ta jalyuzi.'
            )
            
            messages.success(request, f'Buyurtma #{order.order_number} muvaffaqiyatli yaratildi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        # URL dan mijozni olish
        customer_id = request.GET.get('customer')
        initial = {}
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
                initial['customer'] = customer
            except Customer.DoesNotExist:
                pass
        
        form = OrderForm(initial=initial)
        formset = OrderItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Yangi buyurtma yaratish',
    }
    
    return render(request, 'orders/form.html', context)


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
        formset = OrderItemFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.updated_by = request.user
            order.save()
            
            formset.save()
            
            # History yaratish
            order.create_history(
                action='updated',
                performed_by=request.user,
                notes='Buyurtma ma\'lumotlari yangilandi'
            )
            
            messages.success(request, f'Buyurtma #{order.order_number} yangilandi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    
    context = {
        'form': form,
        'formset': formset,
        'order': order,
        'title': f'#{order.order_number} buyurtmasini tahrirlash',
    }
    
    return render(request, 'orders/form.html', context)


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
    
    # To'lovlari bo'lgan buyurtmalarni o'chirish mumkin emas
    if order.payments.exists():
        messages.error(request, 'Bu buyurtmaning to\'lovlari mavjud. Avval to\'lovlarni o\'chiring!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        order_number = order.order_number
        customer_name = order.customer.get_full_name()
        order.delete()
        messages.success(request, f'Buyurtma #{order_number} ({customer_name}) o\'chirildi!')
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
        messages.error(request, 'Sizda status o\'zgartirish huquqi yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.updated_by = request.user
            
            # Status-specific updates
            if new_status == 'measuring' and not order.measured_by:
                order.measured_by = request.user
            elif new_status == 'processing' and not order.processed_by:
                order.processed_by = request.user
            elif new_status == 'installed' and not order.installed_by:
                order.installed_by = request.user
            elif new_status == 'cancelled':
                order.cancelled_by = request.user
                from django.utils import timezone
                order.cancelled_date = timezone.now().date()
                if notes:
                    order.cancellation_reason = notes
            
            order.save()
            
            # History yaratish
            order.create_history(
                action='status_changed',
                performed_by=request.user,
                notes=f'Status: {old_status} → {new_status}. {notes}'
            )
            
            messages.success(request, f'Buyurtma statusiga o\'zgartirildi: {order.get_status_display()}')
            return redirect('orders:detail', pk=pk)
        else:
            messages.error(request, 'Noto\'g\'ri status!')
    
    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'orders/status_update.html', context)


@login_required
def order_add_item(request, pk):
    """
    Buyurtmaga jalyuzi qo'shish
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda jalyuzi qo\'shish huquqi yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.order = order
            item.save()
            
            messages.success(request, 'Jalyuzi qo\'shildi!')
            return redirect('orders:detail', pk=pk)
    else:
        form = OrderItemForm()
    
    context = {
        'form': form,
        'order': order,
        'title': f'#{order.order_number} ga jalyuzi qo\'shish',
    }
    
    return render(request, 'orders/add_item.html', context)


@login_required
def order_print(request, pk):
    """
    Buyurtmani chop etish uchun sahifa
    """
    order = get_object_or_404(
        Order.objects.select_related('customer', 'created_by')
        .prefetch_related('items', 'payments'),
        pk=pk
    )
    
    context = {
        'order': order,
        'items': order.items.all(),
        'payments': order.payments.filter(is_confirmed=True).order_by('payment_date'),
    }
    
    return render(request, 'orders/print.html', context)