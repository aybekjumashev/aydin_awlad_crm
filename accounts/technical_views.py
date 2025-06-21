# accounts/technical_views.py - TUZATILGAN VERSIYA (installation_date olib tashlandi)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.forms import modelformset_factory
from datetime import date, timedelta

from orders.models import Order, OrderItem
from orders.forms import OrderItemForm
from payments.models import Payment


@login_required
def technical_dashboard(request):
    """Texnik xodim uchun maxsus dashboard"""
    
    user = request.user
    today = date.today()
    
    # Mening vazifalarim
    my_orders = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user)
    ).exclude(status__in=['installed', 'cancelled']).select_related('customer')
    
    # Bugungi vazifalar
    today_tasks = []
    
    # O'lchov vazifalari
    if user.can_measure:
        measuring_today = my_orders.filter(
            assigned_measurer=user,
            status='measuring'
        )
        for order in measuring_today:
            today_tasks.append({
                'order': order,
                'task_type': 'measure',
                'task_name': 'O\'lchov olish',
                'icon': 'bi-rulers',
                'color': 'info',
                'url': f'/orders/{order.pk}/measurement/'
            })
    
    # Ishlab chiqarish vazifalari
    if user.can_manufacture:
        manufacturing_today = my_orders.filter(
            assigned_manufacturer=user,
            status='processing'
        )
        for order in manufacturing_today:
            today_tasks.append({
                'order': order,
                'task_type': 'manufacture',
                'task_name': 'Ishlab chiqarish',
                'icon': 'bi-tools',
                'color': 'warning',
                'url': f'/orders/{order.pk}/manufacturing/'
            })
    
    # O'rnatish vazifalari
    if user.can_install:
        installation_today = my_orders.filter(
            assigned_installer=user,
            status='installing'
        )
        for order in installation_today:
            today_tasks.append({
                'order': order,
                'task_type': 'install',
                'task_name': 'O\'rnatish',
                'icon': 'bi-house-gear',
                'color': 'success',
                'url': f'/orders/{order.pk}/installation/'
            })
    
    # Statistika
    stats = {
        'total_assigned': my_orders.count(),
        'measuring': my_orders.filter(status='measuring').count(),
        'processing': my_orders.filter(status='processing').count(),
        'installing': my_orders.filter(status='installing').count(),
        'today_tasks': len(today_tasks),
    }
    
    context = {
        'today_tasks': today_tasks,
        'my_orders': my_orders[:10],  # Oxirgi 10 ta
        'stats': stats,
        'user': user,
        'title': 'Texnik xodim paneli'
    }
    
    return render(request, 'accounts/technical_dashboard.html', context)


@login_required
def my_tasks(request):
    """Mening vazifalarim sahifasi"""
    
    user = request.user
    
    # Foydalanuvchi texnik xodim ekanligini tekshirish
    if not user.is_technical:
        messages.error(request, 'Bu sahifa faqat texnik xodimlar uchun!')
        return redirect('dashboard')
    
    # Filter parametrlari
    status_filter = request.GET.get('status', 'active')
    task_type = request.GET.get('task_type', 'all')
    
    # Mening buyurtmalarim
    orders = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user)
    ).select_related('customer').distinct()
    
    # Status bo'yicha filtrlash
    if status_filter == 'active':
        orders = orders.exclude(status__in=['installed', 'cancelled'])
    elif status_filter == 'completed':
        orders = orders.filter(status='installed')
    elif status_filter == 'overdue':
        # TUZATILDI: installation_date olib tashlandi
        orders = orders.filter(
            Q(measurement_date__lt=timezone.now(), status='measuring')
        )
    
    # Vazifa turi bo'yicha filtrlash
    if task_type == 'measure' and user.can_measure:
        orders = orders.filter(assigned_measurer=user, status='measuring')
    elif task_type == 'manufacture' and user.can_manufacture:
        orders = orders.filter(assigned_manufacturer=user, status='processing')
    elif task_type == 'install' and user.can_install:
        orders = orders.filter(assigned_installer=user, status='installing')
    
    orders = orders.order_by('-created_at')
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'task_type': task_type,
        'user': user,
        'title': 'Mening vazifalarim'
    }
    
    return render(request, 'accounts/my_tasks.html', context)


@login_required
def measurement_form(request, order_id):
    """O'lchov olish formasi"""
    
    order = get_object_or_404(Order, pk=order_id)
    user = request.user
    
    # Huquqlarni tekshirish
    if not (user.can_measure or user.is_manager or user.is_admin):
        messages.error(request, 'O\'lchov olish huquqingiz yo\'q!')
        return redirect('orders:detail', pk=order.pk)
    
    # Buyurtma holati tekshiruvi
    if order.status != 'measuring':
        messages.error(request, 'Bu buyurtma o\'lchov bosqichida emas!')
        return redirect('orders:detail', pk=order.pk)
    
    # POST so'rov - O'lchov yakunlash
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'complete_measurement':
            # O'lchov yakunlash
            order.assigned_measurer = user
            order.measurement_completed_date = timezone.now()
            order.status = 'processing'  # Ishlab chiqarishga yuborish
            order.save()
            
            messages.success(
                request,
                f'O\'lchov muvaffaqiyatli yakunlandi! '
                f'Buyurtma ishlab chiqarishga yuborildi.'
            )
            return redirect('orders:detail', pk=order.pk)
    
    context = {
        'order': order,
        'title': f'O\'lchov olish - #{order.order_number}'
    }
    
    return render(request, 'accounts/measurement_simple.html', context)


@login_required
def manufacturing_task(request, order_id):
    """Ishlab chiqarish vazifasi"""
    
    order = get_object_or_404(Order, pk=order_id)
    user = request.user
    
    # Huquqlarni tekshirish
    if not (user.can_manufacture or user.is_manager or user.is_admin):
        messages.error(request, 'Ishlab chiqarish huquqingiz yo\'q!')
        return redirect('orders:detail', pk=order.pk)
    
    # Buyurtma holati
    if order.status != 'processing':
        messages.error(request, 'Bu buyurtma ishlab chiqarish bosqichida emas!')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'complete':
            # Ishlab chiqarishni tugatish
            order.assigned_manufacturer = user
            order.production_completed_date = timezone.now()
            order.status = 'installing'
            order.save()
            
            messages.success(
                request,
                f'Ishlab chiqarish yakunlandi! '
                f'Buyurtma o\'rnatishga tayyor.'
            )
            return redirect('orders:detail', pk=order.pk)
    
    context = {
        'order': order,
        'title': f'Ishlab chiqarish - #{order.order_number}'
    }
    
    return render(request, 'accounts/manufacturing_task.html', context)


@login_required
def installation_task(request, order_id):
    """O'rnatish vazifasi"""
    
    order = get_object_or_404(Order, pk=order_id)
    user = request.user
    
    # Huquqlarni tekshirish
    if not (user.can_install or user.is_manager or user.is_admin):
        messages.error(request, 'O\'rnatish huquqingiz yo\'q!')
        return redirect('orders:detail', pk=order.pk)
    
    # Buyurtma holati
    if order.status != 'installing':
        messages.error(request, 'Bu buyurtma o\'rnatish bosqichida emas!')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'complete':
            # O'rnatishni tugatish
            order.assigned_installer = user
            order.installation_completed_date = timezone.now()
            order.status = 'installed'
            order.save()
            
            messages.success(
                request,
                f'O\'rnatish muvaffaqiyatli yakunlandi! '
                f'Buyurtma tayyor.'
            )
            return redirect('orders:detail', pk=order.pk)
    
    context = {
        'order': order,
        'title': f'O\'rnatish - #{order.order_number}'
    }
    
    return render(request, 'accounts/installation_task.html', context)