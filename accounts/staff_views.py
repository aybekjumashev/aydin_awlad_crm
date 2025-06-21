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
    Texnik xodim tafsilotlari
    """
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('staff:list')
    
    staff_member = get_object_or_404(User, pk=pk, role='technical')
    
    # Xodimning statistikalari
    stats = {
        'total_assigned_orders': Order.objects.filter(
            Q(assigned_measurer=staff_member) |
            Q(assigned_manufacturer=staff_member) |
            Q(assigned_installer=staff_member)
        ).count(),
        'completed_orders': Order.objects.filter(
            Q(assigned_measurer=staff_member) |
            Q(assigned_manufacturer=staff_member) |
            Q(assigned_installer=staff_member),
            status='installed'
        ).count(),
        'active_orders': Order.objects.filter(
            Q(assigned_measurer=staff_member) |
            Q(assigned_manufacturer=staff_member) |
            Q(assigned_installer=staff_member)
        ).exclude(status__in=['installed', 'cancelled']).count(),
    }
    
    # Oxirgi buyurtmalar
    recent_orders = Order.objects.filter(
        Q(assigned_measurer=staff_member) |
        Q(assigned_manufacturer=staff_member) |
        Q(assigned_installer=staff_member)
    ).select_related('customer').order_by('-created_at')[:10]
    
    context = {
        'staff_member': staff_member,
        'stats': stats,
        'recent_orders': recent_orders,
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