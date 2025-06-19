# orders/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Order, OrderItem, OrderStatusHistory
from .forms import OrderForm, OrderItemFormSet, OrderFilterForm, MeasurementForm, AreaCalculatorForm
from customers.models import Customer

from decimal import Decimal
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt



@login_required
def order_list(request):
    """
    Buyurtmalar ro'yxati
    """
    if not (request.user.is_manager() or request.user.is_admin() or request.user.is_technician()):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    orders = Order.objects.select_related('customer').prefetch_related('items')
    filter_form = OrderFilterForm(request.GET)
    
    # Filtrlash
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        status = filter_form.cleaned_data.get('status')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        
        if search:
            orders = orders.filter(
                Q(order_number__icontains=search) |
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__phone__icontains=search) |
                Q(address__icontains=search)
            )
        
        if status:
            orders = orders.filter(status=status)
        
        if date_from:
            orders = orders.filter(created_at__date__gte=date_from)
        
        if date_to:
            orders = orders.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(orders.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # Statistika
    stats = {
        'total_orders': Order.objects.count(),
        'new_orders': Order.objects.filter(status='new').count(),
        'measuring_orders': Order.objects.filter(status='measuring').count(),
        'processing_orders': Order.objects.filter(status='processing').count(),
        'installed_orders': Order.objects.filter(status='installed').count(),
    }
    
    context = {
        'orders': orders,
        'filter_form': filter_form,
        'stats': stats,
    }
    
    return render(request, 'orders/list.html', context)


@login_required
def order_detail(request, pk):
    """
    Buyurtma tafsilotlari
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Buyurtma elementlari
    items = order.items.all()
    
    context = {
        'order': order,
        'items': items,
    }
    
    return render(request, 'orders/detail.html', context)


@login_required
def order_add(request):
    """
    Yangi buyurtma qo'shish
    """
    if not (request.user.is_manager() or request.user.is_admin() or 
            (request.user.is_technician() and request.user.can_create_order)):
        messages.error(request, 'Sizda buyurtma yaratish huquqi yo\'q!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.updated_by = request.user
            order.save()
            
            # Buyurtma elementlarini saqlash
            formset.instance = order
            formset.save()
            
            messages.success(request, f'Buyurtma {order.order_number} muvaffaqiyatli yaratildi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderForm()
        formset = OrderItemFormSet()
        
        # Agar customer_id URL parametrida berilgan bo'lsa
        customer_id = request.GET.get('customer_id')
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
                form.fields['customer'].initial = customer
                form.fields['address'].initial = customer.address
            except Customer.DoesNotExist:
                pass
    
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
    
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda buyurtmani tahrirlash huquqi yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.updated_by = request.user
            order.save()
            
            formset.save()
            
            messages.success(request, f'Buyurtma {order.order_number} yangilandi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    
    context = {
        'form': form,
        'formset': formset,
        'order': order,
        'title': f'Buyurtma {order.order_number} ni tahrirlash',
    }
    
    return render(request, 'orders/form.html', context)


@login_required
def order_delete(request, pk):
    """
    Buyurtmani o'chirish
    """
    order = get_object_or_404(Order, pk=pk)
    
    if not request.user.is_admin():
        messages.error(request, 'Faqat admin buyurtmani o\'chira oladi!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        order_number = order.order_number
        customer_name = order.customer.get_full_name()
        order.delete()
        
        messages.success(request, f'Buyurtma {order_number} ({customer_name}) o\'chirildi!')
        return redirect('orders:list')
    
    context = {
        'order': order,
        'items_count': order.items.count(),
    }
    
    return render(request, 'orders/delete.html', context)


@login_required
def order_list(request):
    """
    Buyurtmalar ro'yxati - Yangilangan versiya
    """
    if not (request.user.is_manager() or request.user.is_admin() or request.user.is_technician()):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    orders = Order.objects.select_related('customer').prefetch_related('items')
    filter_form = OrderFilterForm(request.GET)
    
    # Filtrlash
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        status = filter_form.cleaned_data.get('status')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        customer = filter_form.cleaned_data.get('customer')
        
        if search:
            orders = orders.filter(
                Q(order_number__icontains=search) |
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__phone__icontains=search) |
                Q(address__icontains=search)
            )
        
        if status:
            orders = orders.filter(status=status)
        
        if date_from:
            orders = orders.filter(created_at__date__gte=date_from)
        
        if date_to:
            orders = orders.filter(created_at__date__lte=date_to)
        
        if customer:
            orders = orders.filter(customer=customer)
    
    # Pagination
    paginator = Paginator(orders.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # Statistika
    stats = {
        'total_orders': Order.objects.count(),
        'new_orders': Order.objects.filter(status='new').count(),
        'measuring_orders': Order.objects.filter(status='measuring').count(),
        'processing_orders': Order.objects.filter(status='processing').count(),
        'installed_orders': Order.objects.filter(status='installed').count(),
    }
    
    context = {
        'orders': orders,
        'filter_form': filter_form,
        'stats': stats,
    }
    
    return render(request, 'orders/list.html', context)


@login_required
def order_detail(request, pk):
    """
    Buyurtma tafsilotlari - Yangilangan versiya
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Buyurtma elementlari
    items = order.items.all()
    
    # Holat tarixi
    status_history = order.status_history.all().order_by('-changed_at')
    
    # To'lovlar
    payments = order.payments.all().order_by('-payment_date')
    
    # Google Maps havolasi
    maps_url = order.get_google_maps_url()
    
    # Maydon va narx hisobi
    total_area = order.total_area()
    total_price = order.total_price()
    total_paid = order.total_paid()
    remaining_debt = order.remaining_debt()
    
    context = {
        'order': order,
        'items': items,
        'status_history': status_history,
        'payments': payments,
        'maps_url': maps_url,
        'stats': {
            'total_items': order.total_items(),
            'total_area': total_area,
            'total_price': total_price,
            'total_paid': total_paid,
            'remaining_debt': remaining_debt,
            'payment_percentage': order.payment_percentage(),
        }
    }
    
    return render(request, 'orders/detail.html', context)


@login_required
def order_add(request):
    """
    Yangi buyurtma qo'shish - Yangilangan versiya
    """
    if not (request.user.is_manager() or request.user.is_admin() or 
            (request.user.is_technician() and request.user.can_create_order)):
        messages.error(request, 'Sizda buyurtma yaratish huquqi yo\'q!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.updated_by = request.user
            order.save()
            
            # Buyurtma elementlarini saqlash
            formset.instance = order
            formset.save()
            
            # Holat tarixini yaratish
            OrderStatusHistory.objects.create(
                order=order,
                old_status=None,
                new_status=order.status,
                changed_by=request.user,
                notes='Yangi buyurtma yaratildi'
            )
            
            messages.success(request, f'Buyurtma {order.order_number} muvaffaqiyatli yaratildi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderForm()
        formset = OrderItemFormSet()
        
        # Agar customer_id URL parametrida berilgan bo'lsa
        customer_id = request.GET.get('customer_id')
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
                form.fields['customer'].initial = customer
                form.fields['address'].initial = customer.address
            except Customer.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Yangi buyurtma yaratish',
    }
    
    return render(request, 'orders/form.html', context)


@login_required
def order_edit(request, pk):
    """
    Buyurtmani tahrirlash - Yangilangan versiya
    """
    order = get_object_or_404(Order, pk=pk)
    
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda buyurtmani tahrirlash huquqi yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    old_status = order.status
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.updated_by = request.user
            order.save()
            
            formset.save()
            
            # Agar holat o'zgargan bo'lsa, tarixga yozish
            if old_status != order.status:
                OrderStatusHistory.objects.create(
                    order=order,
                    old_status=old_status,
                    new_status=order.status,
                    changed_by=request.user,
                    notes=f'Holat o\'zgartirildi: {old_status} -> {order.status}'
                )
            
            messages.success(request, f'Buyurtma {order.order_number} yangilandi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    
    context = {
        'form': form,
        'formset': formset,
        'order': order,
        'title': f'Buyurtma {order.order_number} ni tahrirlash',
    }
    
    return render(request, 'orders/form.html', context)


@login_required
def order_measure(request, pk):
    """
    O'lchov olish sahifasi - GPS ma'lumotlari bilan
    """
    order = get_object_or_404(Order, pk=pk)
    
    if not (request.user.is_manager() or request.user.is_admin() or 
            (request.user.is_technician() and request.user.can_measure)):
        messages.error(request, 'Sizda o\'lchov olish huquqi yo\'q!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        form = MeasurementForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            old_status = order.status
            
            order = form.save(commit=False)
            order.status = 'processing'  # O'lchov olinguandan keyin ishlab chiqarishga
            order.measured_by = request.user
            order.measurement_date = timezone.now()
            order.updated_by = request.user
            order.save()
            
            formset.save()
            
            # Holat tarixiga yozish
            OrderStatusHistory.objects.create(
                order=order,
                old_status=old_status,
                new_status='processing',
                changed_by=request.user,
                notes='O\'lchov olindi, ishlab chiqarishga yuborildi'
            )
            
            messages.success(request, f'Buyurtma {order.order_number} uchun o\'lchov olindi!')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = MeasurementForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    
    context = {
        'form': form,
        'formset': formset,
        'order': order,
        'title': f'O\'lchov olish - {order.order_number}',
    }
    
    return render(request, 'orders/measure.html', context)


@login_required
def area_calculator(request):
    """
    Maydon kalkulyatori sahifasi
    """
    results = None
    
    if request.method == 'POST':
        form = AreaCalculatorForm(request.POST)
        if form.is_valid():
            results = form.calculate_results()
    else:
        form = AreaCalculatorForm()
    
    context = {
        'form': form,
        'results': results,
    }
    
    return render(request, 'orders/area_calculator.html', context)


@csrf_exempt
@login_required
def ajax_calculate_price(request):
    """
    AJAX orqali narxni hisoblash
    """
    if request.method == 'POST':
        try:
            width = Decimal(request.POST.get('width', 0))
            height = Decimal(request.POST.get('height', 0))
            quantity = int(request.POST.get('quantity', 1))
            price_per_sqm = Decimal(request.POST.get('price_per_sqm', 0))
            
            # Bir dona uchun maydon (m²)
            area_one = (width / 100) * (height / 100)
            
            # Umumiy maydon
            total_area = area_one * quantity
            
            # Narxlar
            price_per_unit = total_area * price_per_sqm if price_per_sqm else 0
            total_price = price_per_unit * quantity
            
            return JsonResponse({
                'success': True,
                'area_one_sqm': float(area_one),
                'total_area_sqm': float(total_area),
                'price_per_unit': float(price_per_unit),
                'total_price': float(total_price),
            })
        
        except (ValueError, TypeError, Exception) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def change_order_status(request, pk):
    """
    Buyurtma holatini o'zgartirish
    """
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Order.STATUS_CHOICES).keys():
            old_status = order.status
            
            # Huquqlarni tekshirish
            can_change = False
            
            if request.user.is_admin() or request.user.is_manager():
                can_change = True
            elif request.user.is_technician():
                if new_status == 'measuring' and request.user.can_measure:
                    can_change = True
                elif new_status == 'processing' and request.user.can_manufacture:
                    can_change = True
                elif new_status == 'installed' and request.user.can_install:
                    can_change = True
                elif new_status == 'cancelled' and request.user.can_cancel_order:
                    can_change = True
            
            if can_change:
                order.status = new_status
                order.updated_by = request.user
                
                # Holat bo'yicha qo'shimcha ma'lumotlar
                if new_status == 'processing':
                    order.measured_by = request.user
                    order.measurement_date = timezone.now()
                elif new_status == 'installed':
                    order.installed_by = request.user
                    order.installation_date = timezone.now()
                
                order.save()
                
                # Holat tarixiga yozish
                OrderStatusHistory.objects.create(
                    order=order,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=request.user,
                    notes=notes or f'Holat o\'zgartirildi: {old_status} -> {new_status}'
                )
                
                messages.success(request, f'Buyurtma holati o\'zgartirildi: {order.get_status_display()}')
            else:
                messages.error(request, 'Sizda bu holatni o\'zgartirish huquqi yo\'q!')
    
    return redirect('orders:detail', pk=pk)


@login_required
def order_delete(request, pk):
    """
    Buyurtmani o'chirish
    """
    order = get_object_or_404(Order, pk=pk)
    
    if not request.user.is_admin():
        messages.error(request, 'Faqat admin buyurtmani o\'chira oladi!')
        return redirect('orders:detail', pk=pk)
    
    if request.method == 'POST':
        order_number = order.order_number
        customer_name = order.customer.get_full_name()
        order.delete()
        
        messages.success(request, f'Buyurtma {order_number} ({customer_name}) o\'chirildi!')
        return redirect('orders:list')
    
    context = {
        'order': order,
        'items_count': order.items.count(),
        'payments_count': order.payments.count(),
    }
    
    return render(request, 'orders/delete.html', context)


@login_required
def orders_map(request):
    """
    Buyurtmalar xaritasi (GPS ma'lumotlari bilan)
    """
    orders_with_location = Order.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('customer')
    
    # Holat bo'yicha filtrlash
    status_filter = request.GET.get('status')
    if status_filter:
        orders_with_location = orders_with_location.filter(status=status_filter)
    
    # JSON formatda ma'lumotlar tayyorlash
    orders_data = []
    for order in orders_with_location:
        orders_data.append({
            'id': order.pk,
            'order_number': order.order_number,
            'customer_name': order.customer.get_full_name(),
            'status': order.status,
            'status_display': order.get_status_display(),
            'latitude': float(order.latitude),
            'longitude': float(order.longitude),
            'address': order.address,
            'total_items': order.total_items(),
            'created_at': order.created_at.strftime('%d.%m.%Y'),
        })
    
    context = {
        'orders_data': orders_data,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status_filter,
    }
    
    return render(request, 'orders/map.html', context)


@login_required
def my_orders(request):
    """
    Mening buyurtmalarim (texnik xodim uchun)
    """
    if not request.user.is_technician():
        messages.error(request, 'Bu sahifa faqat texnik xodimlar uchun!')
        return redirect('dashboard')
    
    # Foydalanuvchi bilan bog'liq buyurtmalar
    orders = Order.objects.filter(
        Q(created_by=request.user) |
        Q(measured_by=request.user) |
        Q(processed_by=request.user) |
        Q(installed_by=request.user)
    ).select_related('customer').distinct().order_by('-created_at')
    
    # Statistika
    my_stats = {
        'created_orders': Order.objects.filter(created_by=request.user).count(),
        'measured_orders': Order.objects.filter(measured_by=request.user).count(),
        'processed_orders': Order.objects.filter(processed_by=request.user).count(),
        'installed_orders': Order.objects.filter(installed_by=request.user).count(),
    }
    
    context = {
        'orders': orders,
        'my_stats': my_stats,
    }
    
    return render(request, 'orders/my_orders.html', context)