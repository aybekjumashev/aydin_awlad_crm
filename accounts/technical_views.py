# accounts/technical_views.py - POOL TIZIMI

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
import logging

# Debug uchun logger
logger = logging.getLogger(__name__)

@login_required
def my_tasks(request):
    """Barcha vazifalar pool'i - texnik xodimlar uchun"""
    if not request.user.is_technical:
        messages.error(request, "Sizda ushbu sahifaga kirish huquqi yo'q.")
        return redirect('dashboard')
    
    user = request.user
    current_time = timezone.now()
    
    # Filtrlash parametrlari
    status_filter = request.GET.get('status', 'active')
    task_type = request.GET.get('task_type', 'all')
    
    # POOL TIZIMI: Barcha buyurtmalarni ko'rsatamiz, lekin foydalanuvchi huquqlariga qarab
    
    # 1. O'lchov vazifalari - barcha 'measuring' buyurtmalar (agar huquqi bo'lsa)
    measuring_orders = []
    if user.can_measure:
        measuring_orders = Order.objects.filter(status='measuring').select_related('customer').order_by('created_at')
    
    # 2. Ishlab chiqarish vazifalari - barcha 'processing' buyurtmalar (agar huquqi bo'lsa)
    manufacturing_orders = []
    if user.can_manufacture:
        manufacturing_orders = Order.objects.filter(status='processing').select_related('customer').order_by('created_at')
    
    # 3. O'rnatish vazifalari - barcha 'installing' buyurtmalar (agar huquqi bo'lsa)
    installing_orders = []
    if user.can_install:
        installing_orders = Order.objects.filter(status='installing').select_related('customer').order_by('created_at')
    
    # 4. Yakunlangan vazifalar - oxirgi 30 kun (faqat o'zi bajargan)
    from datetime import date, timedelta
    thirty_days_ago = date.today() - timedelta(days=30)
    completed_orders = Order.objects.filter(
        status='installed',
        installation_completed_date__gte=thirty_days_ago
    ).select_related('customer').order_by('-installation_completed_date')[:20]
    
    # 5. Barcha faol vazifalar (status bo'yicha)
    if status_filter == 'active':
        all_active_orders = Order.objects.exclude(status__in=['installed', 'cancelled']).select_related('customer')
    elif status_filter == 'completed':
        all_active_orders = completed_orders
    else:
        all_active_orders = Order.objects.all().select_related('customer')
    
    # Vazifa turi bo'yicha filtrlash
    if task_type == 'measure' and user.can_measure:
        filtered_orders = measuring_orders
    elif task_type == 'manufacture' and user.can_manufacture:
        filtered_orders = manufacturing_orders
    elif task_type == 'install' and user.can_install:
        filtered_orders = installing_orders
    elif task_type == 'completed':
        filtered_orders = completed_orders
    else:
        # Barcha faol vazifalar (foydalanuvchi huquqlariga qarab)
        filtered_orders = []
        if user.can_measure:
            filtered_orders.extend(measuring_orders)
        if user.can_manufacture:
            filtered_orders.extend(manufacturing_orders)
        if user.can_install:
            filtered_orders.extend(installing_orders)
        
        # Takroriy elementlarni olib tashlash
        filtered_orders = list(set(filtered_orders))
        filtered_orders.sort(key=lambda x: x.created_at, reverse=True)
    
    # Statistikalar
    measuring_count = len(measuring_orders)
    manufacturing_count = len(manufacturing_orders)
    installing_count = len(installing_orders)
    completed_count = completed_orders.count() if hasattr(completed_orders, 'count') else len(completed_orders)
    total_tasks = measuring_count + manufacturing_count + installing_count
    
    # Bu oyning yakunlangan vazifalari (faqat o'zi bajargan)
    this_month = date.today().replace(day=1)
    completed_this_month = Order.objects.filter(
        status='installed',
        installation_completed_date__gte=this_month
    ).count()
    
    # Mening hozirgi vazifalarim (tayinlangan, lekin yakunlanmagan)
    my_current_tasks = Order.objects.filter(
        ).exclude(status__in=['installed', 'cancelled']).count()
    context = {
        # Vazifa ro'yxatlari
        'all_orders': filtered_orders,
        'measuring_orders': measuring_orders,
        'manufacturing_orders': manufacturing_orders,
        'installing_orders': installing_orders,
        'completed_orders': completed_orders,
        
        # Statistikalar
        'measuring_count': measuring_count,
        'manufacturing_count': manufacturing_count,
        'installing_count': installing_count,
        'completed_count': completed_count,
        'total_tasks': total_tasks,
        'completed_this_month': completed_this_month,
        'my_current_tasks': my_current_tasks,
        
        # Pool tizimi
        'pool_mode': True,
        'status_filter': status_filter,
        'task_type': task_type,
        
        # Qo'shimcha
        'current_time': current_time,
        'page_title': 'Vazifalar Pool\'i'
    }
    
    return render(request, 'technical/my_tasks.html', context)

@login_required
def take_task(request, order_id, task_type):
    """Vazifani o'ziga olish (Pool dan)"""
    if not request.user.is_technical:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('dashboard')
    
    user = request.user
    order = get_object_or_404(Order, id=order_id)
    
    # Vazifa turini tekshirish va huquqni tasdiqlash
    if task_type == 'measure':
        if not user.can_measure or order.status != 'measuring':
            messages.error(request, "Bu vazifani olish mumkin emas.")
            return redirect('technical:my_tasks')
        
        # Agar boshqa kimgadir tayinlangan bo'lsa
        if order.assigned_measurer and order.assigned_measurer != user:
            messages.warning(request, f"Bu vazifa allaqachon {order.assigned_measurer.get_full_name()} ga tayinlangan.")
            return redirect('technical:my_tasks')
        
        order.assigned_measurer = user
        order.save()
        messages.success(request, f"O'lchov vazifasi sizga tayinlandi. Buyurtma #{order.order_number}")
        return redirect('technical:measurement', order_id=order.id)
        
    elif task_type == 'manufacture':
        if not user.can_manufacture or order.status != 'processing':
            messages.error(request, "Bu vazifani olish mumkin emas.")
            return redirect('technical:my_tasks')
            
        if order.assigned_manufacturer and order.assigned_manufacturer != user:
            messages.warning(request, f"Bu vazifa allaqachon {order.assigned_manufacturer.get_full_name()} ga tayinlangan.")
            return redirect('technical:my_tasks')
            
        order.assigned_manufacturer = user
        order.save()
        messages.success(request, f"Ishlab chiqarish vazifasi sizga tayinlandi. Buyurtma #{order.order_number}")
        return redirect('technical:manufacturing', order_id=order.id)
        
    elif task_type == 'install':
        if not user.can_install or order.status != 'installing':
            messages.error(request, "Bu vazifani olish mumkin emas.")
            return redirect('technical:my_tasks')
            
        if order.assigned_installer and order.assigned_installer != user:
            messages.warning(request, f"Bu vazifa allaqachon {order.assigned_installer.get_full_name()} ga tayinlangan.")
            return redirect('technical:my_tasks')
            
        order.assigned_installer = user
        order.save()
        messages.success(request, f"O'rnatish vazifasi sizga tayinlandi. Buyurtma #{order.order_number}")
        return redirect('technical:installation', order_id=order.id)
    
    messages.error(request, "Noma'lum vazifa turi.")
    return redirect('technical:my_tasks')

@login_required
def measurement_form(request, order_id):
    """O'lchov olish formi - GPS koordinatalar bilan"""
    if not request.user.is_technical or not request.user.can_measure:
        messages.error(request, "Sizda o'lchov olish huquqi yo'q.")
        return redirect('dashboard')
    
    order = get_object_or_404(Order, id=order_id, status='measuring')
    

    # Agar hali tayinlanmagan bo'lsa, o'ziga tayinlash
    if not order.assigned_measurer:
        order.assigned_measurer = request.user
        order.save()
        messages.info(request, "Vazifa sizga tayinlandi.")
    
    if request.method == 'POST':
        try:
            measurement_notes = request.POST.get('measurement_notes', '')
            item_count_str = request.POST.get('item_count', '0')
            
            # GPS koordinatlarni olish
            measurement_latitude = request.POST.get('measurement_latitude')
            measurement_longitude = request.POST.get('measurement_longitude')
            measurement_location_accuracy = request.POST.get('measurement_location_accuracy')
            
            try:
                item_count = int(item_count_str)
            except ValueError:
                messages.error(request, "Jalyuzlar soni noto'g'ri kiritilgan.")
                return render(request, 'technical/measurement_form.html', {'order': order})
            
            if item_count <= 0:
                messages.error(request, "Kamida bitta jalyuzi qo'shishingiz kerak.")
                return render(request, 'technical/measurement_form.html', {'order': order})
            
            # Mavjud itemlarni tozalash
            order.items.all().delete()
            
            total_amount = Decimal('0')
            created_items = []
            
            for i in range(item_count):
                width = request.POST.get(f'width_{i}')
                height = request.POST.get(f'height_{i}')
                blind_type = request.POST.get(f'blind_type_{i}')
                material_type = request.POST.get(f'material_type_{i}')
                installation_type = request.POST.get(f'installation_type_{i}')
                mechanism_type = request.POST.get(f'mechanism_type_{i}')
                cornice_type = request.POST.get(f'cornice_type_{i}')
                unit_price = request.POST.get(f'unit_price_{i}')
                quantity = request.POST.get(f'quantity_{i}', 1)
                notes = request.POST.get(f'notes_{i}', '')

                
                if not width or not height or not blind_type or not unit_price:
                    continue
                
                try:
                    width_int = int(width)
                    height_int = int(height)
                    unit_price_decimal = Decimal(str(unit_price))
                    quantity_int = int(quantity) if quantity else 1
                    
                    if width_int <= 0 or height_int <= 0 or unit_price_decimal < 0:
                        continue
                    
                    item = OrderItem.objects.create(
                        order=order,
                        blind_type=blind_type,
                        width=width_int,
                        height=height_int,
                        material=material_type or '',
                        installation_type=installation_type or '',
                        mechanism=mechanism_type or '',
                        cornice_type=cornice_type or '',
                        unit_price=unit_price_decimal,
                        quantity=quantity_int,
                        notes=notes
                    )
                    
                    created_items.append(item)
                    total_amount += item.total_price
                    
                except (ValueError, TypeError):
                    continue
            
            if not created_items:
                messages.error(request, "Hech qanday jalyuzi yaratilmadi. Ma'lumotlarni to'g'ri to'ldiring.")
                return render(request, 'technical/measurement_form.html', {'order': order})
            
            # Avans to'lov
            advance_payment = request.POST.get('advance_payment')
            if advance_payment and float(advance_payment) > 0:
                try:
                    payment = Payment.objects.create(
                        order=order,
                        amount=Decimal(advance_payment),
                        payment_method=request.POST.get('payment_method', 'cash'),
                        payment_type='prepayment',
                        payment_date=timezone.now(),
                        received_by=request.user,
                        notes='O\'lchov paytida qabul qilingan avans to\'lov',
                        status='confirmed'
                    )
                    order.paid_amount = Decimal(advance_payment)
                except Exception as e:
                    messages.warning(request, "Avans to'lov saqlanmadi, lekin o'lchov yakunlandi.")
            
            # GPS koordinatlarni saqlash
            gps_info = ""
            if measurement_latitude and measurement_longitude:
                try:
                    # Koordinatlarni float formatda tekshirish
                    lat = float(measurement_latitude)
                    lng = float(measurement_longitude)
                    accuracy = measurement_location_accuracy or "Noma'lum"
                    
                    # GPS ma'lumotlarni order modeliga saqlash
                    order.measurement_latitude = lat
                    order.measurement_longitude = lng
                    order.measurement_location_accuracy = accuracy
                    
                    gps_info = f"\nGPS koordinatlar: {lat:.6f}, {lng:.6f} (Aniqlik: {accuracy}m)"
                    messages.success(request, "GPS joylashuv ma'lumotlari saqlandi.")
                    
                except (ValueError, TypeError):
                    messages.warning(request, "GPS koordinatlar noto'g'ri formatda. Saqlanmadi.")
            else:
                messages.info(request, "GPS koordinatlar kiritilmagan.")
            
            # Buyurtmani yangilash
            order.total_amount = total_amount
            order.measurement_notes = measurement_notes

            current_notes = order.notes or ''
            measurement_info = f"{measurement_notes}{gps_info}"
            order.notes = f"{current_notes}\n[O'lchash yakunlandi] {measurement_info}".strip()

            order.status = 'processing'
            order.measurement_completed_date = timezone.now()
            order.update_payment_status()
            order.save()
            
            messages.success(request, f"O'lchov ma'lumotlari muvaffaqiyatli saqlandi! {len(created_items)} ta jalyuzi qo'shildi.")
            return redirect('technical:my_tasks')
            
        except Exception as e:
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
    
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
    
    order = get_object_or_404(Order, id=order_id, status='processing')
    

    # Agar hali tayinlanmagan bo'lsa, o'ziga tayinlash
    if not order.assigned_manufacturer:
        order.assigned_manufacturer = request.user
        order.save()
        messages.info(request, "Vazifa sizga tayinlandi.")
    
    if request.method == 'POST':
        manufacturing_notes = request.POST.get('manufacturing_notes', '')
        
        order.status = 'installing'
        order.production_completed_date = timezone.now()
        
        current_notes = order.notes or ''
        manufacturing_info = f"{manufacturing_notes}"
        order.notes = f"{current_notes}\n[Ishlab chiqarish yakunlandi] {manufacturing_info}".strip()
        
        order.save()
        
        messages.success(request, "Ishlab chiqarish yakunlandi. Buyurtma o'rnatishga tayyor.")
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
    
    order = get_object_or_404(Order, id=order_id, status='installing')

    # Agar hali tayinlanmagan bo'lsa, o'ziga tayinlash
    if not order.assigned_installer:
        order.assigned_installer = request.user
        order.save()
        messages.info(request, "Vazifa sizga tayinlandi.")
    
    if request.method == 'POST':
        try:
            installation_notes = request.POST.get('installation_notes', '')
            installation_address = request.POST.get('installation_address', '')
            
            # Qolgan to'lov
            remaining_payment = request.POST.get('remaining_payment')
            if remaining_payment and float(remaining_payment) > 0:
                try:
                    payment = Payment.objects.create(
                        order=order,
                        amount=Decimal(remaining_payment),
                        payment_method=request.POST.get('payment_method', 'cash'),
                        payment_type='final',
                        payment_date=timezone.now(),
                        received_by=request.user,
                        notes='O\'rnatish paytida qabul qilingan to\'lov',
                        status='confirmed'
                    )
                    order.paid_amount += Decimal(remaining_payment)
                except Exception as e:
                    messages.warning(request, "To'lov saqlanmadi, lekin o'rnatish yakunlandi.")
            
            # Buyurtmani yakunlash
            order.status = 'installed'
            order.installation_completed_date = timezone.now()
            
            current_notes = order.notes or ''
            installation_info = f"{installation_notes}"
            order.notes = f"{current_notes}\n[O'rnatish yakunlandi] {installation_info}".strip()
            
            order.save()
            
            messages.success(request, "Buyurtma muvaffaqiyatli o'rnatildi va yakunlandi.")
            return redirect('technical:my_tasks')
            
        except Exception as e:
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
    
    # Qolgan summa hisoblash
    remaining_amount = order.total_amount - order.paid_amount if order.total_amount and order.paid_amount else order.total_amount or Decimal('0')
    
    context = {
        'order': order,
        'remaining_amount': remaining_amount,
        'page_title': 'O\'rnatish',
    }
    
    return render(request, 'technical/installation_task.html', context)

@login_required
def technical_dashboard(request):
    """Texnik xodim dashboard sahifasi"""
    if not request.user.is_technical:
        messages.error(request, "Sizda ushbu sahifaga kirish huquqi yo'q.")
        return redirect('dashboard')
    
    user = request.user
    
    # Pool statistikalari
    total_measuring = Order.objects.filter(status='measuring').count()
    total_manufacturing = Order.objects.filter(status='processing').count()
    total_installing = Order.objects.filter(status='installing').count()
    
    # Mening vazifalarim
    my_orders = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user)
    ).exclude(status__in=['installed', 'cancelled']).select_related('customer')
    
    # Oxirgi 5 ta vazifa
    recent_tasks = my_orders.order_by('-created_at')[:5]
    
    context = {
        'total_measuring': total_measuring,
        'total_manufacturing': total_manufacturing,
        'total_installing': total_installing,
        'my_tasks_count': my_orders.count(),
        'recent_tasks': recent_tasks,
        'page_title': 'Texnik Dashboard'
    }
    
    return render(request, 'technical/dashboard.html', context)