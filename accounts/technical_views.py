# accounts/technical_views.py - POOL TIZIMI

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from orders.models import Order, OrderItem, Customer
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

    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        address = request.POST.get('address')
        notes = request.POST.get('notes')
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                Order.objects.create(customer=customer, address=address, notes=notes)
                messages.success(request, "Buyurtma muvaffaqiyatli yaratildi.")
            except Customer.DoesNotExist:
                messages.error(request, "Mijoz topilmadi.")
        else:
            messages.error(request, "Mijoz tanlanmadi.")
        
        return redirect('technical:my_tasks')

    
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
def customer_list(request):
    """Mijozlar ro'yxati"""
    if not request.user.is_technical:
        messages.error(request, "Sizda mijozlar ro'yxati huquqi yo'q.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        Customer.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            fathers_name=request.POST.get('fathers_name'),
            passport=request.POST.get('passport'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            notes=request.POST.get('notes'),
            birth_date=request.POST.get('birth_date'),
        )
        messages.success(request, "Mijoz muvaffaqiyatli qo'shildi.")
        return redirect('technical:customers_for_tech_url')
    
    customers = Customer.objects.all()
    paginator = Paginator(customers, 
                          per_page=20)  
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'page_title': 'Mijozlar ro\'yxati'
    }
    
    return render(request, 'technical/customer_list.html', context)


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
    

    
    if request.method == 'POST':
        try:
            measurement_notes = request.POST.get('measurement_notes', '')
            item_count_str = request.POST.get('item_count', '0')
            
            # GPS koordinatlarni olish
            measurement_latitude = request.POST.get('measurement_latitude')
            measurement_longitude = request.POST.get('measurement_longitude')
            measurement_location_accuracy = request.POST.get('measurement_location_accuracy')
            installation_scheduled_date = request.POST.get('installation_scheduled_date')
            
            try:
                item_count = int(item_count_str)
            except ValueError:
                messages.error(request, "Jalyuzlar soni noto'g'ri kiritilgan.")
                return render(request, 'technical/measurement_form.html', {'order': order})
            
            if item_count <= 0:
                messages.error(request, "Kamida bitta jalyuzi qo'shishingiz kerak.")
                return render(request, 'technical/measurement_form.html', {'order': order})
            
            # Mavjud itemlarni tozalash - FAQAT formani submit qilinganda
            order.items.all().delete()
            
            total_amount = Decimal('0')
            created_items = []
            
            for i in range(item_count):
                xona = request.POST.get(f'area_{i}')
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
                is_measured = request.POST.get(f'is_measured_{i}', 'off') == 'on'

                
                if not width or not height or not blind_type or not unit_price:
                    continue
                
                try:
                    width_int = int(width)
                    height_int = int(height)
                    unit_price_decimal = Decimal(str(unit_price))
                    quantity_int = int(quantity) if quantity else 1
                    
                    if width_int <= 0 or height_int <= 0 or unit_price_decimal < 0:
                        continue
                    
                    # Display value'larni model choice value'larga mapping
                    # BLIND_TYPE_CHOICES mapping
                    blind_type_mapping = {
                        'Gorizontal jalyuzi': 'horizontal',
                        'Vertikal jalyuzi': 'vertical',
                        'Rollo parda': 'roller',
                        'Plisse parda': 'pleated',
                        'Bambuk jalyuzi': 'bamboo',
                        'Yog\'och jalyuzi': 'wooden',
                        'Mato jalyuzi': 'fabric'
                    }
                    
                    # MATERIAL_CHOICES mapping
                    material_mapping = {
                        'Alyuminiy': 'aluminum',
                        'Plastik': 'plastic',
                        'Yog\'och': 'wood',
                        'Mato': 'fabric',
                        'Bambuk': 'bamboo',
                        'Kompozit': 'composite'
                    }
                    
                    # INSTALLATION_TYPE_CHOICES mapping
                    installation_mapping = {
                        'Devorga o\'rnatish': 'wall',
                        'Shiftga o\'rnatish': 'ceiling',
                        'Deraza romiga o\'rnatish': 'window_frame',
                        'Ichki o\'rnatish': 'niche'
                    }
                    
                    # MECHANISM_CHOICES mapping
                    mechanism_mapping = {
                        'Ip bilan boshqarish': 'cord',
                        'Zanjir bilan boshqarish': 'chain',
                        'Tayoqcha bilan boshqarish': 'wand',
                        'Elektr motor': 'motorized',
                        'Masofadan boshqarish': 'remote',
                        'Aqlli boshqarish': 'smart'
                    }
                            
                    
                    print(f"DEBUG: Creating item {i} with data:")
                    print(f"  - blind_type: {blind_type} -> {blind_type_mapping.get(blind_type, 'horizontal')}")
                    print(f"  - material: {material_type} -> {material_mapping.get(material_type, 'plastic')}")
                    print(f"  - installation: {installation_type} -> {installation_mapping.get(installation_type, 'wall')}")
                    print(f"  - mechanism: {mechanism_type} -> {mechanism_mapping.get(mechanism_type, 'cord')}")
                    
                    item = OrderItem.objects.create(
                        order=order,
                        blind_type=blind_type_mapping.get(blind_type, 'horizontal'),
                        width=width_int,
                        height=height_int,
                        material=material_mapping.get(material_type, 'plastic'),
                        installation_type=installation_mapping.get(installation_type, 'wall'),
                        mechanism=mechanism_mapping.get(mechanism_type, 'cord'),
                        cornice_type='standard',  # Default qiymat
                        unit_price=unit_price_decimal,
                        quantity=quantity_int,
                        notes=notes,
                        room_name=xona,
                        is_measured=is_measured
                    )
                    
                    print(f"DEBUG: Item created with ID: {item.id}")
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
                        amount=Decimal(str(advance_payment)),
                        payment_method=request.POST.get('payment_method', 'cash'),
                        payment_type='prepayment',
                        payment_date=timezone.now(),
                        received_by=request.user,
                        notes='O\'lchov paytida qabul qilingan avans to\'lov',
                        status='confirmed'
                    )
                    order.paid_amount = Decimal(str(advance_payment))
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
                    
                except (ValueError, TypeError):
                    messages.warning(request, "GPS koordinatlar noto'g'ri formatda. Saqlanmadi.")
            else:
                messages.info(request, "GPS koordinatlar kiritilmagan.")
            
            # Buyurtmani yangilash
            order.total_amount = total_amount
            order.measurement_notes = measurement_notes
            order.installation_scheduled_date = installation_scheduled_date

            current_notes = order.notes or ''
            measurement_info = f"{measurement_notes}{gps_info}"
            order.notes = f"{current_notes}\n[O'lchash yakunlandi] {measurement_info}".strip()
            
            # Checkbox bo'yicha statusni o'zgartirish yoki saqlash
            if request.POST.get('advance_payment_checkbox'):
                order.status = 'processing'
                order.measurement_completed_date = timezone.now()
                status_message = "O'lchov yakunlandi va ishlab chiqarishga yuborildi!"
            else:
                # Status o'zgartirilmasdan saqlanadi
                status_message = "O'lchov ma'lumotlari vaqtinchalik saqlandi. Keyinroq to'ldirishingiz mumkin."
            
            order.update_payment_status()
            order.save()
            
            return redirect('technical:my_tasks')
            
        except Exception as e:
            messages.error(request, f"Xatolik yuz berdi: {str(e)}")
    
    # ✅ CONTEXT'GA MAVJUD MA'LUMOTLARNI QO'SHISH
    # Mavjud order item'larni olish va JavaScript uchun tayyorlash
    print(f"DEBUG: Order {order.id} uchun itemlar soni: {order.items.count()}")
    
    # Display value mapping'lar (JavaScript bilan moslash uchun)
    blind_type_display = {
        'horizontal': 'Gorizontal jalyuzi',
        'vertical': 'Vertikal jalyuzi',
        'roller': 'Rollo parda',
        'pleated': 'Plisse parda',
        'bamboo': 'Bambuk jalyuzi',
        'wooden': 'Yog\'och jalyuzi',
        'fabric': 'Mato jalyuzi'
    }
    
    material_display = {
        'aluminum': 'Alyuminiy',
        'plastic': 'Plastik',
        'wood': 'Yog\'och',
        'fabric': 'Mato',
        'bamboo': 'Bambuk',
        'composite': 'Kompozit'
    }
    
    installation_display = {
        'wall': 'Devorga o\'rnatish',
        'ceiling': 'Shiftga o\'rnatish',
        'window_frame': 'Deraza romiga o\'rnatish',
        'niche': 'Ichki o\'rnatish'
    }
    
    mechanism_display = {
        'cord': 'Ip bilan boshqarish',
        'chain': 'Zanjir bilan boshqarish',
        'wand': 'Tayoqcha bilan boshqarish',
        'motorized': 'Elektr motor',
        'remote': 'Masofadan boshqarish',
        'smart': 'Aqlli boshqarish'
    }
    
    existing_items_data = []
    for item in order.items.all():
        print(f"DEBUG: Item {item.id} - {item.blind_type} - {item.width}x{item.height}")
        
        # Display name'larni JavaScript uchun tayyorlash
        item_data = {
            'blind_type_raw': item.blind_type,  # Raw model value
            'blind_type': blind_type_display.get(item.blind_type, item.blind_type),  # Display value
            'width': item.width,
            'height': item.height,
            'material_raw': item.material,  # Raw model value
            'material': material_display.get(item.material, item.material),  # Display value
            'installation_type_raw': item.installation_type,  # Raw model value
            'installation_type': installation_display.get(item.installation_type, item.installation_type),  # Display value
            'mechanism_raw': item.mechanism,  # Raw model value
            'mechanism': mechanism_display.get(item.mechanism, item.mechanism),  # Display value
            'cornice_type': item.cornice_type,
            'unit_price': float(item.unit_price),
            'quantity': item.quantity,
            'notes': item.notes or '',
            'room_name': item.room_name or '',
            'is_measured': item.is_measured
        }
        existing_items_data.append(item_data)
        print(f"DEBUG: Item data: {item_data}")
    
    print(f"DEBUG: existing_items_data: {existing_items_data}")
    
    context = {
        'order': order,
        'page_title': 'O\'lchov olish',
        'existing_items': existing_items_data,  # JavaScript uchun tayyor ma'lumotlar
        'existing_items_raw': list(order.items.all()),  # Template uchun raw QuerySet
        'existing_items_count': len(existing_items_data),  # Debug uchun
        'has_existing_gps': order.has_gps_location,  # GPS mavjudligi
        'existing_gps_lat': float(order.measurement_latitude) if order.measurement_latitude else None,
        'existing_gps_lng': float(order.measurement_longitude) if order.measurement_longitude else None,
        'existing_gps_accuracy': order.measurement_location_accuracy or '',
        'existing_installation_date': order.installation_scheduled_date.strftime('%Y-%m-%d') if order.installation_scheduled_date else '',
        'existing_measurement_notes': order.measurement_notes or '',
        'debug': True,  # Debug rejimini yoqish
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
                        amount=Decimal(str(remaining_payment)),
                        payment_method=request.POST.get('payment_method', 'cash'),
                        payment_type='final',
                        payment_date=timezone.now(),
                        received_by=request.user,
                        notes='O\'rnatish paytida qabul qilingan to\'lov',
                        status='confirmed'
                    )
                    order.paid_amount += Decimal(str(remaining_payment))
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




# Avto-taklif ro‘yxati
def search_customers(request):
    query = request.GET.get('customer_number', '')[:10]
    customers = Customer.objects.filter(phone__icontains=query)[:5]
    results = [{'number': c.phone, 'name': c.get_full_name()} for c in customers]
    return JsonResponse({'results': results})

# Tanlangan mijoz haqida to‘liq info
def get_customer_info(request):
    number = request.GET.get('customer_number')
    try:
        customer = Customer.objects.get(phone=number)
        return JsonResponse({
            'id': customer.pk,
            'name': customer.get_full_name(),
            'address': customer.address
        })
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)









