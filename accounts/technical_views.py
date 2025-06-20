# accounts/technical_views.py - YANGI FAYL
# Texnik xodimlar uchun maxsus view'lar

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.forms import modelformset_factory
from datetime import date, timedelta

from orders.models import Order, OrderItem
# Import'larni vaqtincha o'chiramiz, keyin qo'shamiz
from orders.forms import OrderItemForm, MeasurementForm
from payments.models import Payment
from .decorators import technical_required


@login_required
@technical_required
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
            status='measuring',
            measurement_date__date=today
        )
        for order in measuring_today:
            today_tasks.append({
                'order': order,
                'task_type': 'measure',
                'task_name': 'O\'lchov olish',
                'icon': 'bi-rulers',
                'color': 'info',
                'time': order.measurement_date
            })
    
    # Ishlab chiqarish vazifalari
    if user.can_manufacture:
        manufacturing = my_orders.filter(
            assigned_manufacturer=user,
            status='processing'
        )
        for order in manufacturing:
            today_tasks.append({
                'order': order,
                'task_type': 'manufacture',
                'task_name': 'Ishlab chiqarish',
                'icon': 'bi-gear-fill',
                'color': 'warning'
            })
    
    # O'rnatish vazifalari
    if user.can_install:
        installation_today = my_orders.filter(
            assigned_installer=user,
            status='installing',
            installation_date__date=today
        )
        for order in installation_today:
            today_tasks.append({
                'order': order,
                'task_type': 'install',
                'task_name': 'O\'rnatish',
                'icon': 'bi-tools',
                'color': 'success',
                'time': order.installation_date
            })
    
    # Statistika
    stats = {
        'total_tasks': my_orders.count(),
        'measuring_tasks': my_orders.filter(
            assigned_measurer=user, 
            status='measuring'
        ).count() if user.can_measure else 0,
        
        'manufacturing_tasks': my_orders.filter(
            assigned_manufacturer=user, 
            status='processing'
        ).count() if user.can_manufacture else 0,
        
        'installation_tasks': my_orders.filter(
            assigned_installer=user, 
            status='installing'
        ).count() if user.can_install else 0,
        
        'completed_this_month': Order.objects.filter(
            Q(assigned_measurer=user) |
            Q(assigned_manufacturer=user) |
            Q(assigned_installer=user),
            status='installed',
            updated_at__month=today.month
        ).count(),
    }
    
    # Kechikkan vazifalar
    overdue_tasks = []
    if user.can_measure:
        overdue_measuring = my_orders.filter(
            assigned_measurer=user,
            status='measuring',
            measurement_date__lt=timezone.now()
        )
        overdue_tasks.extend(overdue_measuring)
    
    if user.can_install:
        overdue_installing = my_orders.filter(
            assigned_installer=user,
            status='installing',
            installation_date__lt=timezone.now()
        )
        overdue_tasks.extend(overdue_installing)
    
    context = {
        'today_tasks': today_tasks,
        'stats': stats,
        'overdue_tasks': overdue_tasks,
        'user': user,
        'current_time': timezone.now(),
    }
    
    return render(request, 'accounts/technical_dashboard.html', context)


@login_required
@technical_required
def my_tasks(request):
    """Mening barcha vazifalarim"""
    
    user = request.user
    
    # Filtrlash
    status_filter = request.GET.get('status', 'active')
    task_type = request.GET.get('task_type', 'all')
    
    # Asosiy so'rov
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
        orders = orders.filter(
            Q(measurement_date__lt=timezone.now(), status='measuring') |
            Q(installation_date__lt=timezone.now(), status='installing')
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
    
    # Tayinlangan o'lchov oluvchini tekshirish
    if (user.is_technical and 
        order.assigned_measurer and 
        order.assigned_measurer != user):
        messages.error(request, 'Bu o\'lchov boshqa xodimga tayinlangan!')
        return redirect('my_tasks')
    
    # Mavjud jalyuzilar
    existing_items = order.items.all()
    
    # Formset yaratish
    OrderItemFormSet = modelformset_factory(
        OrderItem,
        form=OrderItemForm,
        extra=1 if not existing_items else 0,
        can_delete=True
    )
    
    if request.method == 'POST':
        formset = OrderItemFormSet(
            request.POST,
            queryset=existing_items,
            prefix='items'
        )
        
        measurement_form = MeasurementForm(request.POST, instance=order)
        
        if formset.is_valid() and measurement_form.is_valid():
            # O'lchov ma'lumotlarini saqlash
            order = measurement_form.save(commit=False)
            order.assigned_measurer = user
            order.measurement_date = timezone.now()
            order.save()
            
            # Jalyuzilarni saqlash
            instances = formset.save(commit=False)
            for instance in instances:
                instance.order = order
                instance.save()
            
            # O'chirilgan jalyuzilar
            for obj in formset.deleted_objects:
                obj.delete()
            
            # Umumiy narxni hisoblash
            order.calculate_total()
            
            # Statusni yangilash
            if order.items.exists():
                order.status = 'processing'
                order.save()
                
                messages.success(
                    request,
                    f'O\'lchov muvaffaqiyatli bajarildi! '
                    f'Buyurtma ishlab chiqarishga yuborildi.'
                )
            else:
                messages.warning(
                    request,
                    'Jalyuzilar qo\'shilmadi. O\'lchov davom etmoqda.'
                )
            
            return redirect('orders:detail', pk=order.pk)
        else:
            messages.error(request, 'Formada xatoliklar mavjud!')
    
    else:
        formset = OrderItemFormSet(queryset=existing_items, prefix='items')
        measurement_form = MeasurementForm(instance=order)
    
    context = {
        'order': order,
        'formset': formset,
        'measurement_form': measurement_form,
        'title': f'O\'lchov olish - #{order.order_number}'
    }
    
    return render(request, 'orders/measurement_form.html', context)


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
    
    # Tayinlangan ishlab chiqaruvchini tekshirish
    if (user.is_technical and 
        order.assigned_manufacturer and 
        order.assigned_manufacturer != user):
        messages.error(request, 'Bu vazifa boshqa xodimga tayinlangan!')
        return redirect('my_tasks')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'start':
            # Ishlab chiqarishni boshlash
            order.assigned_manufacturer = user
            order.manufacturing_start_date = timezone.now()
            order.save()
            
            messages.success(
                request,
                f'Ishlab chiqarish boshlandi! Tayyor bo\'lgach "Tayyor" tugmasini bosing.'
            )
        
        elif action == 'complete':
            # Ishlab chiqarishni tugatish
            order.manufacturing_end_date = timezone.now()
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
    
    return render(request, 'orders/manufacturing_task.html', context)


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
    
    # Tayinlangan o'rnatuvchini tekshirish
    if (user.is_technical and 
        order.assigned_installer and 
        order.assigned_installer != user):
        messages.error(request, 'Bu vazifa boshqa xodimga tayinlangan!')
        return redirect('my_tasks')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'start':
            # O'rnatishni boshlash
            order.assigned_installer = user
            order.installation_start_date = timezone.now()
            order.save()
            
            messages.success(
                request,
                f'O\'rnatish boshlandi! Tugagach "Yakunlash" tugmasini bosing.'
            )
        
        elif action == 'complete':
            # O'rnatishni yakunlash
            order.installation_date = timezone.now()
            order.status = 'installed'
            order.save()
            
            messages.success(
                request,
                f'Buyurtma muvaffaqiyatli yakunlandi! '
                f'Mijoz bilan final to\'lov qilishingiz mumkin.'
            )
        
        return redirect('orders:detail', pk=order.pk)
    
    context = {
        'order': order,
        'title': f'O\'rnatish - #{order.order_number}'
    }
    
    return render(request, 'orders/installation_task.html', context)