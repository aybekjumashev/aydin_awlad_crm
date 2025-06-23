# accounts/technical_views.py - BARCHA ORDERLAR KO'RINADIGAN VERSIYA

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
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
    
    # Foydalanuvchi huquqlariga qarab vazifalarni olish (barcha orderlardan)
    my_measuring_orders = Order.objects.filter(
        status='measuring'
    ).count() if user.can_measure else 0
    
    my_manufacturing_orders = Order.objects.filter(
        status='processing'
    ).count() if user.can_manufacture else 0
    
    my_installation_orders = Order.objects.filter(
        status='installing'
    ).count() if user.can_install else 0
    
    # Umumiy statistika (barcha orderlar)
    total_assigned = Order.objects.count()
    completed_orders = Order.objects.filter(status='installed').count()
    
    # Bugungi vazifalar (barcha orderlardan huquqlariga qarab)
    today_tasks = []
    
    # O'lchov vazifalari (barcha measuring orderlar)
    if user.can_measure:
        measuring_tasks = Order.objects.filter(
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
    
    # Ishlab chiqarish vazifalari (barcha processing orderlar)
    if user.can_manufacture:
        manufacturing_tasks = Order.objects.filter(
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
    
    # O'rnatish vazifalari (barcha installing orderlar)
    if user.can_install:
        installation_tasks = Order.objects.filter(
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
        'today_tasks': today_tasks[:10],
        'page_title': 'Texnik xodim paneli'
    }
    
    return render(request, 'accounts/technical_dashboard.html', context)

@login_required
def my_tasks(request):
    """Texnik xodim uchun mening vazifalarim - BARCHA ORDERLAR"""
    
    if not hasattr(request.user, 'is_technical') or not request.user.is_technical:
        messages.error(request, 'Bu sahifa faqat texnik xodimlar uchun!')
        return redirect('dashboard')
    
    user = request.user
    current_time = timezone.now()
    
    # DEBUG: Konsolda ko'rsatish
    print(f"DEBUG: User: {user.username}, Role: {user.role}")
    print(f"DEBUG: can_measure: {user.can_measure}")
    print(f"DEBUG: can_manufacture: {user.can_manufacture}")
    print(f"DEBUG: can_install: {user.can_install}")
    
    # ✅ TUZATILDI: BARCHA buyurtmalarni ko'rsatish (faqat tayinlanganlarni emas)
    # Faol buyurtmalar (tugallanmagan va bekor qilinmaganlar)
    all_orders = Order.objects.exclude(
        status__in=['installed', 'cancelled']
    ).select_related('customer').order_by('-created_at')
    
    print(f"DEBUG: Barcha faol buyurtmalar: {all_orders.count()}")
    
    # Filtrlash
    status_filter = request.GET.get('status', 'active')
    task_type = request.GET.get('task_type', 'all')
    
    if status_filter == 'completed':
        all_orders = Order.objects.filter(
            status='installed'
        ).select_related('customer').order_by('-created_at')
    elif status_filter == 'overdue':
        # Kechikkan vazifalar
        all_orders = all_orders.filter(
            Q(measurement_date__lt=current_time, status='measuring') |
            Q(installation_date__lt=current_time, status='installing')
        )
    elif status_filter == 'all':
        # Barcha buyurtmalar (tugallangan va bekor qilinganlarni ham)
        all_orders = Order.objects.all().select_related('customer').order_by('-created_at')
    
    # Vazifa turiga qarab filtrlash (foydalanuvchi huquqlariga qarab)
    if task_type == 'measure' and user.can_measure:
        all_orders = all_orders.filter(status='measuring')
    elif task_type == 'manufacture' and user.can_manufacture:
        all_orders = all_orders.filter(status='processing')
    elif task_type == 'install' and user.can_install:
        all_orders = all_orders.filter(status='installing')
    
    print(f"DEBUG: Filtrdan keyin buyurtmalar: {all_orders.count()}")
    
    # Sahifalash
    paginator = Paginator(all_orders, 12)  # Har sahifada 12 ta
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # Bu oyning yakunlangan vazifalari (foydalanuvchi uchun)
    from datetime import date
    this_month = date.today().replace(day=1)
    completed_this_month = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user),
        status='installed',
        installation_completed_date__gte=this_month
    ).count()
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'task_type': task_type,
        'current_time': current_time,
        'completed_this_month': completed_this_month,
        'title': 'Mening vazifalarim'
    }
    
    return render(request, 'technical/my_tasks.html', context)

@login_required
def measurement_form(request, order_id):
    """O'lchov olish formi - Har qanday measuring orderga ruxsat"""
    if not request.user.is_technical or not request.user.can_measure:
        messages.error(request, "Sizda o'lchov olish huquqi yo'q.")
        return redirect('dashboard')
    
    # ✅ TUZATILDI: Faqat status tekshirish, tayinlanish emas
    order = get_object_or_404(Order, id=order_id, status='measuring')
    
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
            
            # Buyurtmani yangilash va o'zini tayinlash
            order.total_amount = total_amount
            order.measurement_notes = measurement_notes
            order.status = 'processing'
            order.measurement_completed_date = timezone.now()
            order.assigned_measurer = request.user  # O'zini tayinlash
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
    """Ishlab chiqarish vazifasi - Har qanday processing orderga ruxsat"""
    if not request.user.is_technical or not request.user.can_manufacture:
        messages.error(request, "Sizda ishlab chiqarish huquqi yo'q.")
        return redirect('dashboard')
    
    # ✅ TUZATILDI: Faqat status tekshirish
    order = get_object_or_404(Order, id=order_id, status='processing')
    
    if request.method == 'POST':
        # Ishlab chiqarish holatini yangilash
        manufacturing_notes = request.POST.get('manufacturing_notes', '')
        
        # Buyurtma holatini yangilash
        if 'complete_manufacturing' in request.POST:
            order.status = 'installing'
            order.production_completed_date = timezone.now()
            order.assigned_manufacturer = request.user  # O'zini tayinlash
            
            # Notes yangilash
            current_notes = order.notes or ''
            order.notes = f"{current_notes}\n[Ishlab chiqarish yakunlandi]: {manufacturing_notes}".strip()
            
            messages.success(request, "Ishlab chiqarish muvaffaqiyatli yakunlandi. Buyurtma o'rnatishga yuborildi.")
        else:
            # Faqat izoh saqlash
            current_notes = order.notes or ''
            order.notes = f"{current_notes}\n[Ishlab chiqarish jarayoni]: {manufacturing_notes}".strip()
            order.assigned_manufacturer = request.user  # O'zini tayinlash
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
    """O'rnatish vazifasi - Har qanday installing orderga ruxsat"""
    if not request.user.is_technical or not request.user.can_install:
        messages.error(request, "Sizda o'rnatish huquqi yo'q.")
        return redirect('dashboard')
    
    # ✅ TUZATILDI: Faqat status tekshirish
    order = get_object_or_404(Order, id=order_id, status='installing')
    
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
        
        # Buyurtmani yakunlash va o'zini tayinlash
        order.status = 'installed'
        order.installation_completed_date = timezone.now()
        order.assigned_installer = request.user  # O'zini tayinlash
        
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