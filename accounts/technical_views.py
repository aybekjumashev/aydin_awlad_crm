# accounts/technical_views.py - TUZATILGAN VERSIYA

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from orders.models import Order

@login_required
def technical_dashboard(request):
    """Texnik xodim dashboard sahifasi"""
    if not request.user.is_technical:
        messages.error(request, "Sizda ushbu sahifaga kirish huquqi yo'q.")
        return redirect('dashboard')
    
    # Texnik xodim uchun statistikalar - barcha tayinlanishlarni hisobga olish
    my_orders = Order.objects.filter(
        Q(assigned_measurer=request.user) |
        Q(assigned_manufacturer=request.user) |
        Q(assigned_installer=request.user)
    )
    
    # Foydalanuvchining huquqlariga qarab vazifalarni filtrlash
    my_measuring_orders = Order.objects.filter(assigned_measurer=request.user) if request.user.can_measure else Order.objects.none()
    my_manufacturing_orders = Order.objects.filter(assigned_manufacturer=request.user) if request.user.can_manufacture else Order.objects.none()
    my_installation_orders = Order.objects.filter(assigned_installer=request.user) if request.user.can_install else Order.objects.none()
    
    context = {
        'total_orders': my_orders.count(),
        'measuring_orders': my_measuring_orders.count(),
        'manufacturing_orders': my_manufacturing_orders.count(),
        'installation_orders': my_installation_orders.count(),
        'pending_orders': my_orders.filter(status__in=['measuring', 'processing']).count(),
        'completed_orders': my_orders.filter(status='installed').count(),
    }
    
    return render(request, 'accounts/technical_dashboard.html', context)

@login_required
def my_tasks(request):
    """Texnik xodimning vazifalari ro'yxati"""
    if not request.user.is_technical:
        messages.error(request, "Sizda ushbu sahifaga kirish huquqi yo'q.")
        return redirect('dashboard')
    
    # Foydalanuvchiga tayinlangan barcha buyurtmalar
    orders = Order.objects.filter(
        Q(assigned_measurer=request.user) |
        Q(assigned_manufacturer=request.user) |
        Q(assigned_installer=request.user)
    ).select_related('customer').order_by('-created_at')
    
    # Huquqlarga qarab vazifalarni ajratish
    measuring_tasks = []
    manufacturing_tasks = []
    installation_tasks = []
    
    for order in orders:
        if order.assigned_measurer == request.user and request.user.can_measure:
            measuring_tasks.append(order)
        if order.assigned_manufacturer == request.user and request.user.can_manufacture:
            manufacturing_tasks.append(order)
        if order.assigned_installer == request.user and request.user.can_install:
            installation_tasks.append(order)
    
    context = {
        'measuring_tasks': measuring_tasks,
        'manufacturing_tasks': manufacturing_tasks,
        'installation_tasks': installation_tasks,
        'all_orders': orders,
        'page_title': 'Mening vazifalarim',
    }
    
    return render(request, 'technical/my_tasks.html', context)

@login_required
def measurement_form(request, order_id):
    """O'lchov olish formi"""
    if not request.user.is_technical or not request.user.can_measure:
        messages.error(request, "Sizda o'lchov olish huquqi yo'q.")
        return redirect('dashboard')
    
    order = get_object_or_404(Order, id=order_id, assigned_measurer=request.user)
    
    if request.method == 'POST':
        # O'lchov ma'lumotlarini saqlash
        measurement_notes = request.POST.get('measurement_notes', '')
        
        # Order itemlarni yangilash
        for item in order.items.all():
            width = request.POST.get(f'width_{item.id}')
            height = request.POST.get(f'height_{item.id}')
            
            if width and height:
                item.width = int(width)
                item.height = int(height)
                item.save()
        
        # Buyurtma holatini yangilash
        order.measurement_notes = measurement_notes
        order.status = 'processing'  # O'lchov tugagandan keyin
        order.save()
        
        messages.success(request, "O'lchov ma'lumotlari muvaffaqiyatli saqlandi.")
        return redirect('technical:my_tasks')
    
    context = {
        'order': order,
        'page_title': 'O\'lchov olish',
    }
    
    return render(request, 'technical/measurement_form.html', context)

@login_required
def manufacturing_task(request, order_id):
    """Ishlab chiqarish vazifasi"""
    if not request.user.is_technical or not request.user.can_manufacture:
        messages.error(request, "Sizda ishlab chiqarish huquqi yo'q.")
        return redirect('dashboard')
    
    order = get_object_or_404(Order, id=order_id, assigned_manufacturer=request.user)
    
    if request.method == 'POST':
        # Ishlab chiqarish holatini yangilash
        manufacturing_notes = request.POST.get('manufacturing_notes', '')
        
        # Buyurtma holatini yangilash
        if 'complete_manufacturing' in request.POST:
            order.status = 'installing'  # Ishlab chiqarish tugagach o'rnatishga
            messages.success(request, "Ishlab chiqarish muvaffaqiyatli yakunlandi.")
        else:
            order.status = 'processing'
            messages.success(request, "Ishlab chiqarish jarayoni saqlandi.")
        
        # Notes maydonini tekshirish (agar mavjud bo'lsa)
        if hasattr(order, 'manufacturing_notes'):
            order.manufacturing_notes = manufacturing_notes
        else:
            # notes maydoniga yozish
            current_notes = order.notes or ''
            order.notes = f"{current_notes}\n[Ishlab chiqarish]: {manufacturing_notes}".strip()
        
        order.save()
        return redirect('technical:my_tasks')
    
    context = {
        'order': order,
        'page_title': 'Ishlab chiqarish',
    }
    
    return render(request, 'technical/manufacturing_task.html', context)

@login_required
def installation_task(request, order_id):
    """O'rnatish vazifasi"""
    if not request.user.is_technical or not request.user.can_install:
        messages.error(request, "Sizda o'rnatish huquqi yo'q.")
        return redirect('dashboard')
    
    order = get_object_or_404(Order, id=order_id, assigned_installer=request.user)
    
    if request.method == 'POST':
        # O'rnatish jarayonini yakunlash
        installation_notes = request.POST.get('installation_notes', '')
        
        # Buyurtma holatini yakunlash
        order.status = 'installed'
        
        # Notes maydonini tekshirish (agar mavjud bo'lsa)
        if hasattr(order, 'installation_notes'):
            order.installation_notes = installation_notes
        else:
            # notes maydoniga yozish
            current_notes = order.notes or ''
            order.notes = f"{current_notes}\n[O'rnatish]: {installation_notes}".strip()
        
        order.save()
        
        messages.success(request, "Buyurtma muvaffaqiyatli o'rnatildi.")
        return redirect('technical:my_tasks')
    
    context = {
        'order': order,
        'page_title': 'O\'rnatish',
    }
    
    return render(request, 'technical/installation_task.html', context)