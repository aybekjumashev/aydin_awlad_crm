# accounts/technical_views.py - TO'LIQ TUZATILGAN VERSIYA

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from orders.models import Order, OrderItem
from payments.models import Payment
from decimal import Decimal

@login_required
def technical_dashboard(request):
    """Texnik xodim dashboard sahifasi"""
    if not request.user.is_technical:
        messages.error(request, "Sizda ushbu sahifaga kirish huquqi yo'q.")
        return redirect('dashboard')
    
    user = request.user
    
    # Foydalanuvchi huquqlariga qarab vazifalarni olish
    my_measuring_orders = Order.objects.filter(
        assigned_measurer=user, 
        status='measuring'
    ).count() if user.can_measure else 0
    
    my_manufacturing_orders = Order.objects.filter(
        assigned_manufacturer=user,
        status='processing'
    ).count() if user.can_manufacture else 0
    
    my_installation_orders = Order.objects.filter(
        assigned_installer=user,
        status='installing'
    ).count() if user.can_install else 0
    
    # Umumiy statistika
    total_assigned = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user)
    ).count()
    
    completed_orders = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user),
        status='installed'
    ).count()
    
    # Bugungi vazifalar
    today_tasks = []
    
    # O'lchov vazifalari
    if user.can_measure:
        measuring_tasks = Order.objects.filter(
            assigned_measurer=user,
            status='measuring'
        ).select_related('customer')[:5]
        
        for order in measuring_tasks:
            today_tasks.append({
                'order': order,
                'task_type': 'measure',
                'task_name': 'O\'lchov olish',
                'icon': 'bi-rulers',
                'color': 'info'
            })
    
    # Ishlab chiqarish vazifalari
    if user.can_manufacture:
        manufacturing_tasks = Order.objects.filter(
            assigned_manufacturer=user,
            status='processing'
        ).select_related('customer')[:5]
        
        for order in manufacturing_tasks:
            today_tasks.append({
                'order': order,
                'task_type': 'manufacture',
                'task_name': 'Ishlab chiqarish',
                'icon': 'bi-tools',
                'color': 'warning'
            })
    
    # O'rnatish vazifalari
    if user.can_install:
        installation_tasks = Order.objects.filter(
            assigned_installer=user,
            status='installing'
        ).select_related('customer')[:5]
        
        for order in installation_tasks:
            today_tasks.append({
                'order': order,
                'task_type': 'install',
                'task_name': 'O\'rnatish',
                'icon': 'bi-house-gear',
                'color': 'success'
            })
    
    context = {
        'measuring_orders': my_measuring_orders,
        'manufacturing_orders': my_manufacturing_orders,
        'installation_orders': my_installation_orders,
        'total_assigned': total_assigned,
        'completed_orders': completed_orders,
        'today_tasks': today_tasks[:10],  # Eng ko'pi 10 ta vazifa
        'page_title': 'Texnik xodim paneli'
    }
    
    return render(request, 'accounts/technical_dashboard.html', context)

@login_required
def my_tasks(request):
    """Texnik xodimning vazifalari ro'yxati"""
    if not request.user.is_technical:
        messages.error(request, "Sizda ushbu sahifaga kirish huquqi yo'q.")
        return redirect('dashboard')
    
    user = request.user
    
    # Huquqlarga qarab vazifalarni ajratish
    measuring_tasks = []
    manufacturing_tasks = []
    installation_tasks = []
    
    # O'lchov vazifalari
    if user.can_measure:
        measuring_tasks = Order.objects.filter(
            assigned_measurer=user,
            status='measuring'
        ).select_related('customer').order_by('-created_at')
    
    # Ishlab chiqarish vazifalari  
    if user.can_manufacture:
        manufacturing_tasks = Order.objects.filter(
            assigned_manufacturer=user,
            status='processing'
        ).select_related('customer').order_by('-created_at')
    
    # O'rnatish vazifalari
    if user.can_install:
        installation_tasks = Order.objects.filter(
            assigned_installer=user,
            status='installing'
        ).select_related('customer').order_by('-created_at')
    
    context = {
        'measuring_tasks': measuring_tasks,
        'manufacturing_tasks': manufacturing_tasks,
        'installation_tasks': installation_tasks,
        'page_title': 'Mening vazifalarim',
    }
    
    return render(request, 'technical/my_tasks.html', context)

@login_required
def measurement_form(request, order_id):
    """O'lchov olish formi - OrderItem yaratish bilan"""
    if not request.user.is_technical or not request.user.can_measure:
        messages.error(request, "Sizda o'lchov olish huquqi yo'q.")
        return redirect('dashboard')
    
    order = get_object_or_404(Order, id=order_id, assigned_measurer=request.user, status='measuring')
    
    if request.method == 'POST':
        try:
            # O'lchov ma'lumotlarini saqlash
            measurement_notes = request.POST.get('measurement_notes', '')
            
            # OrderItem'larni yaratish yoki yangilash
            item_count = int(request.POST.get('item_count', 1))
            
            # Mavjud itemlarni tozalash (agar qayta o'lchansa)
            order.items.all().delete()
            
            total_amount = Decimal('0')
            
            for i in range(item_count):
                # Har bir item uchun ma'lumotlar
                width = request.POST.get(f'width_{i}')
                height = request.POST.get(f'height_{i}')
                blind_type = request.POST.get(f'blind_type_{i}')
                material_type = request.POST.get(f'material_type_{i}')
                installation_type = request.POST.get(f'installation_type_{i}')
                mechanism_type = request.POST.get(f'mechanism_type_{i}')
                cornice_type = request.POST.get(f'cornice_type_{i}')
                unit_price = request.POST.get(f'unit_price_{i}')
                quantity = request.POST.get(f'quantity_{i}', 1)
                
                if width and height and blind_type and unit_price:
                    item = OrderItem.objects.create(
                        order=order,
                        blind_type=blind_type,
                        width=int(width),
                        height=int(height),
                        material_type=material_type or '',
                        installation_type=installation_type or '',
                        mechanism_type=mechanism_type or '',
                        cornice_type=cornice_type or '',
                        unit_price=Decimal(unit_price),
                        quantity=int(quantity),
                        notes=request.POST.get(f'notes_{i}', '')
                    )
                    
                    total_amount += item.total_price
            
            # Avans to'lovni qo'shish (agar mavjud bo'lsa)
            advance_payment = request.POST.get('advance_payment')
            if advance_payment and float(advance_payment) > 0:
                Payment.objects.create(
                    order=order,
                    amount=Decimal(advance_payment),
                    payment_method=request.POST.get('payment_method', 'cash'),
                    payment_type='advance',
                    notes='O\'lchov paytida qabul qilingan avans to\'lov',
                    status='confirmed'
                )
                order.paid_amount = Decimal(advance_payment)
            
            # Buyurtmani yangilash
            order.total_amount = total_amount
            order.measurement_notes = measurement_notes
            order.status = 'processing'  # O'lchov tugagach ishlab chiqarishga
            order.measurement_completed_date = timezone.now()
            order.save()
            
            messages.success(request, "O'lchov ma'lumotlari muvaffaqiyatli saqlandi va buyurtma ishlab chiqarishga yuborildi.")
            return redirect('technical:my_tasks')
            
        except (ValueError, TypeError) as e:
            messages.error(request, f"Ma'lumotlarda xatolik: {str(e)}")
    
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
    
    order = get_object_or_404(Order, id=order_id, assigned_manufacturer=request.user, status='processing')
    
    if request.method == 'POST':
        # Ishlab chiqarish holatini yangilash
        manufacturing_notes = request.POST.get('manufacturing_notes', '')
        
        # Buyurtma holatini yangilash
        if 'complete_manufacturing' in request.POST:
            order.status = 'installing'  # Ishlab chiqarish tugagach o'rnatishga
            order.production_completed_date = timezone.now()
            
            # Notes yangilash
            current_notes = order.notes or ''
            order.notes = f"{current_notes}\n[Ishlab chiqarish yakunlandi]: {manufacturing_notes}".strip()
            
            messages.success(request, "Ishlab chiqarish muvaffaqiyatli yakunlandi. Buyurtma o'rnatishga yuborildi.")
        else:
            # Faqat izoh saqlash
            current_notes = order.notes or ''
            order.notes = f"{current_notes}\n[Ishlab chiqarish jarayoni]: {manufacturing_notes}".strip()
            messages.success(request, "Ishlab chiqarish jarayoni saqlandi.")
        
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
    
    order = get_object_or_404(Order, id=order_id, assigned_installer=request.user, status='installing')
    
    if request.method == 'POST':
        # O'rnatish ma'lumotlarini saqlash
        installation_notes = request.POST.get('installation_notes', '')
        installation_address = request.POST.get('installation_address', '')
        
        # Qolgan to'lovni qo'shish
        remaining_payment = request.POST.get('remaining_payment')
        if remaining_payment and float(remaining_payment) > 0:
            Payment.objects.create(
                order=order,
                amount=Decimal(remaining_payment),
                payment_method=request.POST.get('payment_method', 'cash'),
                payment_type='final',
                notes='O\'rnatish paytida qabul qilingan to\'lov',
                status='confirmed'
            )
            order.paid_amount += Decimal(remaining_payment)
        
        # Buyurtmani yakunlash
        order.status = 'installed'
        order.installation_completed_date = timezone.now()
        
        # Notes yangilash
        current_notes = order.notes or ''
        installation_info = f"O'rnatish manzili: {installation_address}\nIzohlar: {installation_notes}"
        order.notes = f"{current_notes}\n[O'rnatish yakunlandi]: {installation_info}".strip()
        
        order.save()
        
        messages.success(request, "Buyurtma muvaffaqiyatli o'rnatildi va yakunlandi.")
        return redirect('technical:my_tasks')
    
    context = {
        'order': order,
        'remaining_amount': order.total_amount - order.paid_amount,
        'page_title': 'O\'rnatish',
    }
    
    return render(request, 'technical/installation_task.html', context)