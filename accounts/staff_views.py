# accounts/staff_views.py - TO'LIQ TUZATILGAN VERSIYA

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import User
from orders.models import Order
from payments.models import Payment


@login_required
def staff_list(request):
    """
    Texnik xodimlar ro'yxati
    """
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda xodimlarni ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    # Texnik xodimlarni olish
    staff_members = User.objects.filter(role='technical').order_by('-date_joined')
    
    context = {
        'staff_members': staff_members,
        'title': 'Texnik xodimlar ro\'yxati'
    }
    
    return render(request, 'accounts/staff_list.html', context)


@login_required
def staff_add(request):
    """
    Yangi texnik xodim qo'shish
    """
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda texnik xodim qo\'shish huquqi yo\'q!')
        return redirect('staff:list')
    
    if request.method == 'POST':
        # Form ma'lumotlarini olish
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        specialist_type = request.POST.get('specialist_type')
        
        # Huquqlar
        can_measure = request.POST.get('can_measure') == 'on'
        can_manufacture = request.POST.get('can_manufacture') == 'on'
        can_install = request.POST.get('can_install') == 'on'
        can_create_order = request.POST.get('can_create_order') == 'on'
        
        # Validatsiya
        if not username or not password:
            messages.error(request, 'Username va parol majburiy!')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Bu username allaqachon mavjud!')
        else:
            try:
                # Yangi texnik xodim yaratish
                staff_member = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    role='technical',
                    specialist_type=specialist_type,
                    can_measure=can_measure,
                    can_manufacture=can_manufacture,
                    can_install=can_install,
                    can_create_order=can_create_order,
                )
                
                messages.success(
                    request, 
                    f'Texnik xodim {staff_member.get_full_name() or staff_member.username} muvaffaqiyatli qo\'shildi!'
                )
                return redirect('staff:detail', pk=staff_member.pk)
                
            except Exception as e:
                messages.error(request, f'Xatolik: {str(e)}')
    
    # Specialist type choices
    specialist_choices = [
        ('measurer', 'O\'lchov oluvchi'),
        ('manufacturer', 'Ishlab chiquvchi'),
        ('installer', 'O\'rnatuvchi'),
        ('universal', 'Universal (barchasi)'),
    ]
    
    context = {
        'specialist_choices': specialist_choices,
        'title': 'Yangi texnik xodim qo\'shish',
    }
    
    return render(request, 'accounts/staff_form.html', context)

@login_required  
def staff_detail(request, pk):
    """
    Texnik xodim tafsilotlari - YAXSHILANGAN VERSIYA
    """
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('staff:list')
    
    staff_member = get_object_or_404(User, pk=pk, role='technical')
    
    # Import qilish kerak bo'lgan modellar
    from django.db.models import Q, Sum, Count
    from orders.models import Order
    from payments.models import Payment  # MUHIM: Payment modelini import qilish
    from django.utils import timezone
    from datetime import timedelta
    
    # ASOSIY STATISTIKALAR - Template bilan mos keluvchi
    stats = {
        # 1. Ishtirok etgan buyurtmalar (created_by field yo'q, shuning uchun ishtirok etgan buyurtmalar)
        'created_orders': Order.objects.filter(
            Q(assigned_measurer=staff_member) |
            Q(assigned_manufacturer=staff_member) |
            Q(assigned_installer=staff_member)
        ).count(),
        
        # 2. O'lchov olgan buyurtmalar
        'measured_orders': Order.objects.filter(
            assigned_measurer=staff_member,
            measurement_completed_date__isnull=False  # O'lchov tugagan
        ).count(),
        
        # 3. Ishlab chiqargan buyurtmalar  
        'processed_orders': Order.objects.filter(
            assigned_manufacturer=staff_member,
            production_completed_date__isnull=False  # Ishlab chiqarish tugagan
        ).count(),
        
        # 4. O'rnatgan buyurtmalar
        'installed_orders': Order.objects.filter(
            assigned_installer=staff_member,
            installation_completed_date__isnull=False  # O'rnatish tugagan
        ).count(),
        
        # 5. Qabul qilgan to'lovlar soni
        'received_payments': Payment.objects.filter(
            received_by=staff_member,
            status='confirmed'  # Faqat tasdiqlangan to'lovlar
        ).count(),
        
        # 6. Jami qabul qilingan summa
        'total_received': Payment.objects.filter(
            received_by=staff_member,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # QO'SHIMCHA FOYDALI STATISTIKALAR
    additional_stats = {
        # Jami tayinlangan buyurtmalar
        'total_assigned_orders': Order.objects.filter(
            Q(assigned_measurer=staff_member) |
            Q(assigned_manufacturer=staff_member) |
            Q(assigned_installer=staff_member)
        ).count(),
        
        # Tugallangan buyurtmalar
        'completed_orders': Order.objects.filter(
            Q(assigned_measurer=staff_member) |
            Q(assigned_manufacturer=staff_member) |
            Q(assigned_installer=staff_member),
            status='installed'
        ).count(),
        
        # Faol (davom etayotgan) buyurtmalar
        'active_orders': Order.objects.filter(
            Q(assigned_measurer=staff_member) |
            Q(assigned_manufacturer=staff_member) |
            Q(assigned_installer=staff_member)
        ).exclude(status__in=['installed', 'cancelled']).count(),
        
        # Bu oyda qabul qilgan to'lovlar
        'month_payments': Payment.objects.filter(
            received_by=staff_member,
            status='confirmed',
            payment_date__month=timezone.now().month,
            payment_date__year=timezone.now().year
        ).count(),
        
        # Bu oyda qabul qilingan summa
        'month_received': Payment.objects.filter(
            received_by=staff_member,
            status='confirmed',
            payment_date__month=timezone.now().month,
            payment_date__year=timezone.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0,
        
        # Bu haftada bajarilgan ishlar
        'week_completed_tasks': Order.objects.filter(
            Q(
                assigned_measurer=staff_member,
                measurement_completed_date__gte=timezone.now() - timedelta(days=7)
            ) |
            Q(
                assigned_manufacturer=staff_member,
                production_completed_date__gte=timezone.now() - timedelta(days=7)
            ) |
            Q(
                assigned_installer=staff_member,
                installation_completed_date__gte=timezone.now() - timedelta(days=7)
            )
        ).count(),
    }
    
    # Statistikalarni birlashtirish
    stats.update(additional_stats)
    
    # So'nggi buyurtmalar (xodim ishtirok etgan)
    recent_orders = Order.objects.filter(
        Q(assigned_measurer=staff_member) |
        Q(assigned_manufacturer=staff_member) |
        Q(assigned_installer=staff_member)
    ).select_related('customer').order_by('-created_at')[:10]
    
    # So'nggi qabul qilgan to'lovlar (xodim qabul qilgan)
    try:
        recent_payments = Payment.objects.filter(
            received_by=staff_member
        ).exclude(
            status__in=['cancelled', 'pending']  # Bekor qilingan va kutilayotganlarni chiqarib tashlash
        ).select_related('order', 'order__customer').order_by('-payment_date')[:5]
    except Exception as e:
        # Agar Payment modeli yoki fieldlari bilan muammo bo'lsa
        recent_payments = []
    
    # SAMARADORLIK HISOBI (Performance Metrics)
    performance_stats = {}
    
    # O'lchov olish samaradorligi
    if staff_member.can_measure:
        measuring_orders = Order.objects.filter(assigned_measurer=staff_member)
        performance_stats['measuring_efficiency'] = {
            'total_assigned': measuring_orders.count(),
            'completed': measuring_orders.filter(measurement_completed_date__isnull=False).count(),
            'pending': measuring_orders.filter(measurement_completed_date__isnull=True).count(),
        }
        # Foiz hisobi
        if performance_stats['measuring_efficiency']['total_assigned'] > 0:
            performance_stats['measuring_efficiency']['completion_rate'] = round(
                (performance_stats['measuring_efficiency']['completed'] / 
                 performance_stats['measuring_efficiency']['total_assigned']) * 100, 1
            )
        else:
            performance_stats['measuring_efficiency']['completion_rate'] = 0
    
    # Ishlab chiqarish samaradorligi  
    if staff_member.can_manufacture:
        manufacturing_orders = Order.objects.filter(assigned_manufacturer=staff_member)
        performance_stats['manufacturing_efficiency'] = {
            'total_assigned': manufacturing_orders.count(),
            'completed': manufacturing_orders.filter(production_completed_date__isnull=False).count(),
            'pending': manufacturing_orders.filter(production_completed_date__isnull=True).count(),
        }
        if performance_stats['manufacturing_efficiency']['total_assigned'] > 0:
            performance_stats['manufacturing_efficiency']['completion_rate'] = round(
                (performance_stats['manufacturing_efficiency']['completed'] / 
                 performance_stats['manufacturing_efficiency']['total_assigned']) * 100, 1
            )
        else:
            performance_stats['manufacturing_efficiency']['completion_rate'] = 0
    
    # O'rnatish samaradorligi
    if staff_member.can_install:
        installing_orders = Order.objects.filter(assigned_installer=staff_member)
        performance_stats['installing_efficiency'] = {
            'total_assigned': installing_orders.count(),
            'completed': installing_orders.filter(installation_completed_date__isnull=False).count(),
            'pending': installing_orders.filter(installation_completed_date__isnull=True).count(),
        }
        if performance_stats['installing_efficiency']['total_assigned'] > 0:
            performance_stats['installing_efficiency']['completion_rate'] = round(
                (performance_stats['installing_efficiency']['completed'] / 
                 performance_stats['installing_efficiency']['total_assigned']) * 100, 1
            )
        else:
            performance_stats['installing_efficiency']['completion_rate'] = 0
    
    stats['performance'] = performance_stats
    
    context = {
        'staff_member': staff_member,
        'stats': stats,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'title': f'{staff_member.get_full_name() or staff_member.username} - Tafsilotlar'
    }
    
    return render(request, 'accounts/staff_detail.html', context)


@login_required
def staff_edit(request, pk):
    """
    Texnik xodim ma'lumotlarini tahrirlash - TO'LIQ ISHLAYDIGNA VERSIYA
    """
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda xodim ma\'lumotlarini tahrirlash huquqi yo\'q!')
        return redirect('staff:detail', pk=pk)
    
    staff_member = get_object_or_404(User, pk=pk, role='technical')
    
    if request.method == 'POST':
        try:
            # Shaxsiy ma'lumotlarni yangilash
            staff_member.first_name = request.POST.get('first_name', '').strip()
            staff_member.last_name = request.POST.get('last_name', '').strip()
            staff_member.email = request.POST.get('email', '').strip()
            staff_member.phone = request.POST.get('phone', '').strip()
            staff_member.specialist_type = request.POST.get('specialist_type', '')
            
            # Huquqlarni yangilash
            staff_member.can_create_order = request.POST.get('can_create_order') == 'on'
            staff_member.can_measure = request.POST.get('can_measure') == 'on'
            staff_member.can_manufacture = request.POST.get('can_manufacture') == 'on'
            staff_member.can_install = request.POST.get('can_install') == 'on'
            staff_member.can_cancel_order = request.POST.get('can_cancel_order') == 'on'
            staff_member.can_manage_payments = request.POST.get('can_manage_payments') == 'on'
            staff_member.can_view_all_orders = request.POST.get('can_view_all_orders') == 'on'
            
            # Saqlash
            staff_member.save()
            
            messages.success(
                request, 
                f'{staff_member.get_full_name() or staff_member.username} ma\'lumotlari yangilandi!'
            )
            return redirect('staff:detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Xatolik: {str(e)}')
    
    context = {
        'staff_member': staff_member,
        'title': f'{staff_member.get_full_name() or staff_member.username} - Tahrirlash'
    }
    
    return render(request, 'accounts/staff_edit.html', context)


@login_required
def staff_reset_password(request, pk):
    """
    Texnik xodim parolini tiklash
    """
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda parol tiklash huquqi yo\'q!')
        return redirect('staff:detail', pk=pk)
    
    staff_member = get_object_or_404(User, pk=pk, role='technical')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not new_password:
            messages.error(request, 'Yangi parol kiritilishi shart!')
        elif len(new_password) < 6:
            messages.error(request, 'Parol kamida 6 ta belgidan iborat bo\'lishi kerak!')
        elif new_password != confirm_password:
            messages.error(request, 'Parollar mos kelmaydi!')
        else:
            staff_member.set_password(new_password)
            staff_member.save()
            
            messages.success(
                request, 
                f'{staff_member.get_full_name() or staff_member.username} ning paroli tiklandi!'
            )
            return redirect('staff:detail', pk=pk)
    
    context = {
        'staff_member': staff_member,
        'title': f'{staff_member.get_full_name() or staff_member.username} - Parol tiklash'
    }
    
    return render(request, 'accounts/staff_reset_password.html', context)


@login_required
def staff_toggle_status(request, pk):
    """
    Texnik xodim faollik holatini o'zgartirish
    """
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda xodim holatini o\'zgartirish huquqi yo\'q!')
        return redirect('staff:detail', pk=pk)
    
    staff_member = get_object_or_404(User, pk=pk, role='technical')
    
    # Faollik holatini o'zgartirish
    staff_member.is_active = not staff_member.is_active
    staff_member.save()
    
    status_text = "faollashtirildi" if staff_member.is_active else "nofaol qilindi"
    messages.success(
        request, 
        f'{staff_member.get_full_name() or staff_member.username} {status_text}!'
    )
    
    return redirect('staff:detail', pk=pk)


@login_required
def staff_delete(request, pk):
    """
    Texnik xodimni o'chirish
    """
    # Faqat admin o'chira oladi
    if not request.user.is_admin:
        messages.error(request, 'Sizda xodimni o\'chirish huquqi yo\'q!')
        return redirect('staff:detail', pk=pk)
    
    staff_member = get_object_or_404(User, pk=pk, role='technical')
    
    # Faol buyurtmalari bor xodimni o'chirish mumkin emas
    active_orders = Order.objects.filter(
        Q(assigned_measurer=staff_member) |
        Q(assigned_manufacturer=staff_member) |
        Q(assigned_installer=staff_member)
    ).exclude(status__in=['installed', 'cancelled']).count()
    
    if active_orders > 0:
        messages.error(
            request, 
            f'Bu xodimda {active_orders} ta faol buyurtma bor. '
            f'Avval buyurtmalarni boshqa xodimlarga tayinlang!'
        )
        return redirect('staff:detail', pk=pk)
    
    if request.method == 'POST':
        staff_name = staff_member.get_full_name() or staff_member.username
        staff_member.delete()
        messages.success(request, f'Texnik xodim {staff_name} o\'chirildi!')
        return redirect('staff:list')
    
    context = {
        'staff_member': staff_member,
        'title': f'{staff_member.get_full_name() or staff_member.username} - O\'chirish'
    }
    
    return render(request, 'accounts/staff_delete.html', context)