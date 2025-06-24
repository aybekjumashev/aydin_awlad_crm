# accounts/technical_views.py - TUZATILGAN VERSIYA

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
def measurement_form(request, order_id):
    """O'lchov olish formi - TUZATILGAN VERSIYA"""
    if not request.user.is_technical or not request.user.can_measure:
        messages.error(request, "Sizda o'lchov olish huquqi yo'q.")
        return redirect('dashboard')
    
    # Faqat status tekshirish
    order = get_object_or_404(Order, id=order_id, status='measuring')
    
    if request.method == 'POST':
        try:
            # ✅ DEBUG: POST ma'lumotlarini tekshirish
            logger.info(f"POST ma'lumotlari: {request.POST}")
            
            # O'lchov ma'lumotlarini saqlash
            measurement_notes = request.POST.get('measurement_notes', '')
            
            # ✅ TUZATILDI: item_count ni to'g'ri olish
            item_count_str = request.POST.get('item_count', '0')
            print(item_count_str)
            try:
                item_count = int(item_count_str)
                logger.info(f"Item count: {item_count}")
            except ValueError:
                logger.error(f"Noto'g'ri item_count: {item_count_str}")
                messages.error(request, "Jalyuzlar soni noto'g'ri kiritilgan.")
                return render(request, 'technical/measurement_form.html', {'order': order})
            
            if item_count <= 0:
                messages.error(request, "Kamida bitta jalyuzi qo'shishingiz kerak.")
                return render(request, 'technical/measurement_form.html', {'order': order})
            
            # Mavjud itemlarni tozalash (agar qayta o'lchansa)
            deleted_count = order.items.all().delete()[0]
            logger.info(f"O'chirilgan itemlar soni: {deleted_count}")
            
            total_amount = Decimal('0')
            created_items = []
            
            # ✅ TUZATILDI: 0 dan item_count gacha
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
                notes = request.POST.get(f'notes_{i}', '')
                
                # ✅ DEBUG: har bir item ma'lumotlarini tekshirish
                logger.info(f"Item {i}: width={width}, height={height}, blind_type={blind_type}, unit_price={unit_price}")
                
                # ✅ TUZATILDI: majburiy fieldlarni tekshirish
                if not width or not height or not blind_type or not unit_price:
                    logger.warning(f"Item {i} da majburiy ma'lumotlar to'ldirilmagan")
                    continue  # Bu itemni o'tkazib yuborish
                
                try:
                    # Ma'lumotlarni konvertatsiya qilish
                    width_int = int(width)
                    height_int = int(height)
                    unit_price_decimal = Decimal(str(unit_price))
                    quantity_int = int(quantity) if quantity else 1
                    
                    # ✅ VALIDATSIYA: o'lchamlar mantiqiy bo'lishi kerak
                    if width_int <= 0 or height_int <= 0:
                        logger.warning(f"Item {i} da noto'g'ri o'lchamlar: {width_int}x{height_int}")
                        continue
                    
                    if unit_price_decimal < 0:
                        logger.warning(f"Item {i} da manfiy narx: {unit_price_decimal}")
                        continue
                    
                    # OrderItem yaratish
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
                    logger.info(f"Item {i} muvaffaqiyatli yaratildi: {item.id}")
                    
                except (ValueError, TypeError) as e:
                    logger.error(f"Item {i} yaratishda xatolik: {str(e)}")
                    continue
            
            # ✅ TEKSHIRISH: kamida bitta item yaratilganmi
            if not created_items:
                messages.error(request, "Hech qanday jalyuzi yaratilmadi. Ma'lumotlarni to'g'ri to'ldiring.")
                return render(request, 'technical/measurement_form.html', {'order': order})
            
            logger.info(f"Jami {len(created_items)} ta item yaratildi. Umumiy summa: {total_amount}")
            
            # ✅ AVANS TO'LOV: payment_date bilan
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
                    logger.info(f"Avans to'lov yaratildi: {payment.id} - {advance_payment} so'm")
                except Exception as e:
                    logger.error(f"Avans to'lov yaratishda xatolik: {str(e)}")
                    messages.warning(request, "Avans to'lov saqlanmadi, lekin o'lchov yakunlandi.")
            
            # Buyurtmani yangilash
            order.total_amount = total_amount
            order.measurement_notes = measurement_notes
            order.status = 'processing'
            order.measurement_completed_date = timezone.now()
            order.assigned_measurer = request.user
            order.save()
            
            logger.info(f"Buyurtma {order.id} muvaffaqiyatli yangilandi")
            
            messages.success(request, f"O'lchov ma'lumotlari muvaffaqiyatli saqlandi! {len(created_items)} ta jalyuzi qo'shildi va buyurtma ishlab chiqarishga yuborildi.")
            return redirect('technical:my_tasks')
            
        except Exception as e:
            logger.error(f"Measurement form da umumiy xatolik: {str(e)}")
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
    
    context = {
        'order': order,
        'page_title': 'O\'lchov olish',
    }
    
    return render(request, 'technical/measurement_form.html', context)

# Qolgan funksiyalar o'zgarmasdan qoladi...

@login_required
def technical_dashboard(request):
    """Texnik xodim dashboard sahifasi"""
    if not request.user.is_technical:
        messages.error(request, "Sizda ushbu sahifaga kirish huquqi yo'q.")
        return redirect('dashboard')
    
    user = request.user
    
    # Mening vazifalarim
    my_orders = Order.objects.filter(
        Q(assigned_measurer=user) |
        Q(assigned_manufacturer=user) |
        Q(assigned_installer=user)
    ).exclude(status__in=['installed', 'cancelled']).select_related('customer')
    
    # Statistikalar
    total_tasks = my_orders.count()
    measuring_tasks = my_orders.filter(status='measuring', assigned_measurer=user).count()
    manufacturing_tasks = my_orders.filter(status='processing', assigned_manufacturer=user).count()
    installing_tasks = my_orders.filter(status='installing', assigned_installer=user).count()
    
    # Oxirgi 5 ta vazifa
    recent_tasks = my_orders.order_by('-created_at')[:5]
    
    context = {
        'total_tasks': total_tasks,
        'measuring_tasks': measuring_tasks,
        'manufacturing_tasks': manufacturing_tasks,
        'installing_tasks': installing_tasks,
        'recent_tasks': recent_tasks,
        'page_title': 'Texnik Dashboard'
    }
    
    return render(request, 'technical/dashboard.html', context)

@login_required
def my_tasks(request):
    """Mening vazifalarim sahifasi"""
    if not request.user.is_technical:
        messages.error(request, "Sizda ushbu sahifaga kirish huquqi yo'q.")
        return redirect('dashboard')
    
    user = request.user
    current_time = timezone.now()
    
    # Filtrlash parametrlari
    status_filter = request.GET.get('status', 'active')
    task_type = request.GET.get('task_type', 'all')
    
    # Asosiy query
    orders_query = Order.objects.filter().select_related('customer').distinct()
    
    # Status bo'yicha filtrlash
    if status_filter == 'active':
        orders_query = orders_query.exclude(status__in=['installed', 'cancelled'])
    elif status_filter == 'completed':
        orders_query = orders_query.filter(status='installed')
    elif status_filter == 'cancelled':
        orders_query = orders_query.filter(status='cancelled')
    
    # Vazifa turi bo'yicha filtrlash
    if task_type == 'measure' and user.can_measure:
        orders_query = orders_query.filter(assigned_measurer=user, status='measuring')
    elif task_type == 'manufacture' and user.can_manufacture:
        orders_query = orders_query.filter(assigned_manufacturer=user, status='processing')
    elif task_type == 'install' and user.can_install:
        orders_query = orders_query.filter(assigned_installer=user, status='installing')
    
    # Pagination
    paginator = Paginator(orders_query.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # Bu oyning yakunlangan vazifalari
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
def manufacturing_task(request, order_id):
    """Ishlab chiqarish vazifasi"""
    if not request.user.is_technical or not request.user.can_manufacture:
        messages.error(request, "Sizda ishlab chiqarish huquqi yo'q.")
        return redirect('dashboard')
    
    order = get_object_or_404(Order, id=order_id, status='processing')
    
    if request.method == 'POST':
        # Ishlab chiqarish ma'lumotlarini saqlash
        manufacturing_notes = request.POST.get('manufacturing_notes', '')
        
        # Buyurtmani keyingi bosqichga o'tkazish
        order.status = 'installing'
        order.production_completed_date = timezone.now()
        order.assigned_manufacturer = request.user
        
        # Notes yangilash
        current_notes = order.notes or ''
        manufacturing_info = f"Ishlab chiqarish izohlar: {manufacturing_notes}"
        order.notes = f"{current_notes}\n[Ishlab chiqarish yakunlandi]: {manufacturing_info}".strip()
        
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
    """O'rnatish vazifasi - TUZATILGAN VERSIYA"""
    if not request.user.is_technical or not request.user.can_install:
        messages.error(request, "Sizda o'rnatish huquqi yo'q.")
        return redirect('dashboard')
    
    order = get_object_or_404(Order, id=order_id, status='installing')
    
    if request.method == 'POST':
        try:
            # O'rnatish ma'lumotlarini saqlash
            installation_notes = request.POST.get('installation_notes', '')
            installation_address = request.POST.get('installation_address', '')
            
            # ✅ TUZATILDI: Qolgan to'lovni qo'shish (payment_date bilan)
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
                    logger.info(f"Qolgan to'lov yaratildi: {payment.id} - {remaining_payment} so'm")
                except Exception as e:
                    logger.error(f"Qolgan to'lov yaratishda xatolik: {str(e)}")
                    messages.warning(request, "To'lov saqlanmadi, lekin o'rnatish yakunlandi.")
            
            # Buyurtmani yakunlash
            order.status = 'installed'
            order.installation_completed_date = timezone.now()
            order.assigned_installer = request.user
            
            # Notes yangilash
            current_notes = order.notes or ''
            installation_info = f"O'rnatish manzili: {installation_address}\nIzohlar: {installation_notes}"
            order.notes = f"{current_notes}\n[O'rnatish yakunlandi]: {installation_info}".strip()
            
            order.save()
            
            logger.info(f"Buyurtma {order.id} muvaffaqiyatli o'rnatildi")
            
            messages.success(request, "Buyurtma muvaffaqiyatli o'rnatildi va yakunlandi.")
            return redirect('technical:my_tasks')
            
        except (ValueError, TypeError) as e:
            logger.error(f"Installation form da xatolik: {str(e)}")
            messages.error(request, f"Ma'lumotlarda xatolik: {str(e)}")
        except Exception as e:
            logger.error(f"Installation form da umumiy xatolik: {str(e)}")
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
    
    # Qolgan summa hisoblash
    remaining_amount = order.total_amount - order.paid_amount if order.total_amount and order.paid_amount else order.total_amount or Decimal('0')
    
    context = {
        'order': order,
        'remaining_amount': remaining_amount,
        'page_title': 'O\'rnatish',
    }
    
    return render(request, 'technical/installation_task.html', context)