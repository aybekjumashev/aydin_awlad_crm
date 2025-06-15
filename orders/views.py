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
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.updated_by = request.user
            
            # Status bo'yicha qo'shimcha ma'lumotlarni yangilash
            if new_status == 'measuring' and not order.measured_by:
                order.measured_by = request.user
                order.measurement_date = timezone.now().date()
            elif new_status == 'processing' and not order.processed_by:
                order.processed_by = request.user
                order.processing_start_date = timezone.now().date()
            elif new_status == 'installed' and not order.installed_by:
                order.installed_by = request.user
                order.installation_date = timezone.now().date()
            elif new_status == 'cancelled':
                order.cancelled_by = request.user
                order.cancelled_date = timezone.now().date()
                if notes:
                    order.cancellation_reason = notes
            
            order.save()
            
            messages.success(
                request, 
                f'Buyurtma #{order.order_number} holati "{old_status}" dan "{new_status}" ga o\'zgartirildi!'
            )
        else:
            messages.error(request, 'Noto\'g\'ri status tanlandi!')
    
    return redirect('orders:detail', pk=pk)


@login_required
def order_item_add(request, pk):
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
            
            messages.success(request, 'Jalyuzi buyurtmaga qo\'shildi!')
            return redirect('orders:detail', pk=pk)
    else:
        form = OrderItemForm()
    
    context = {
        'form': form,
        'order': order,
        'title': f'Buyurtma #{order.order_number}ga jalyuzi qo\'shish',
    }
    
    return render(request, 'orders/item_form.html', context)


@login_required
def order_item_edit(request, pk):
    """
    Jalyuzini tahrirlash
    """
    item = get_object_or_404(OrderItem, pk=pk)
    order = item.order
    
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda jalyuzini tahrirlash huquqi yo\'q!')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        form = OrderItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Jalyuzi ma\'lumotlari yangilandi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderItemForm(instance=item)
    
    context = {
        'form': form,
        'item': item,
        'order': order,
        'title': f'Jalyuzini tahrirlash',
    }
    
    return render(request, 'orders/item_form.html', context)


@login_required
def order_item_delete(request, pk):
    """
    Jalyuzini o'chirish
    """
    item = get_object_or_404(OrderItem, pk=pk)
    order = item.order
    
    # Huquqlarni tekshirish
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda jalyuzini o\'chirish huquqi yo\'q!')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Jalyuzi o\'chirildi!')
        return redirect('orders:detail', pk=order.pk)
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def order_pdf(request, pk):
    """
    Buyurtmani PDF formatida export qilish
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Bu funksiya kelajakda WeasyPrint bilan implement qilinadi
    messages.info(request, 'PDF export funksiyasi hali tayyor emas')
    return redirect('orders:detail', pk=pk)


@login_required
def order_ajax_stats(request):
    """
    AJAX orqali buyurtmalar statistikasi
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Faqat AJAX so\'rovlar'}, status=400)
    
    stats = {
        'new_orders': Order.objects.filter(status='new').count(),
        'measuring_orders': Order.objects.filter(status='measuring').count(),
        'processing_orders': Order.objects.filter(status='processing').count(),
        'completed_orders': Order.objects.filter(status='installed').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
    }
    
    return JsonResponse(stats)