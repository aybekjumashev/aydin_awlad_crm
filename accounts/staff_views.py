# accounts/staff_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import User
from .forms import TechnicianForm, TechnicianEditForm, StaffPasswordResetForm  # ✅ BU IMPORT QO'SHILDI
from orders.models import Order
from payments.models import Payment


@login_required
def staff_list(request):
    """
    Texnik xodimlar ro'yxati
    """
    # Faqat menejer va admin ko'ra oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    # Faqat texnik xodimlarni olish - prefetch bilan statistika
    staff = User.objects.filter(role='technician').select_related().prefetch_related(
        'created_orders',
        'received_payments'
    ).order_by('-created_at')
    
    # Qidiruv
    search = request.GET.get('search')
    if search:
        staff = staff.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Faollik filtri
    status = request.GET.get('status')
    if status == 'active':
        staff = staff.filter(is_active=True)
    elif status == 'inactive':
        staff = staff.filter(is_active=False)
    
    # Annotation bilan statistika qo'shish
    staff = staff.annotate(
        total_orders_count=Count('created_orders', distinct=True),
        received_payments_count=Count('received_payments', distinct=True),
        total_payments_sum=Sum('received_payments__amount')
    )
    
    # Pagination
    paginator = Paginator(staff, 20)
    page_number = request.GET.get('page')
    staff_page = paginator.get_page(page_number)
    
    # Umumiy statistika
    stats = {
        'total_staff': User.objects.filter(role='technician').count(),
        'active_staff': User.objects.filter(role='technician', is_active=True).count(),
        'inactive_staff': User.objects.filter(role='technician', is_active=False).count(),
    }
    
    context = {
        'staff': staff_page,
        'search': search,
        'status': status,
        'stats': stats,
    }
    
    return render(request, 'accounts/staff_list.html', context)


@login_required
def staff_add(request):
    """
    Yangi texnik xodim qo'shish
    """
    # Faqat menejer va admin qo'sha oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda texnik xodim qo\'shish huquqi yo\'q!')
        return redirect('staff:list')
    
    if request.method == 'POST':
        form = TechnicianForm(request.POST)
        if form.is_valid():
            staff_member = form.save()
            messages.success(
                request, 
                f'Texnik xodim {staff_member.get_full_name() or staff_member.username} muvaffaqiyatli qo\'shildi!'
            )
            return redirect('staff:detail', pk=staff_member.pk)
    else:
        form = TechnicianForm()
    
    context = {
        'form': form,
        'title': 'Yangi texnik xodim qo\'shish',
    }
    
    return render(request, 'accounts/staff_form.html', context)


@login_required  
def staff_detail(request, pk):
    """
    Texnik xodim tafsilotlari
    """
    # Faqat menejer va admin ko'ra oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    staff_member = get_object_or_404(User, pk=pk, role='technician')
    
    # Xodim statistikasi
    stats = {
        'created_orders': staff_member.created_orders.count(),
        'received_payments': staff_member.received_payments.count(),
        'total_received': staff_member.received_payments.filter(
            is_confirmed=True
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # So'nggi buyurtmalar
    recent_orders = staff_member.created_orders.select_related('customer').order_by('-created_at')[:10]
    
    # So'nggi to'lovlar
    recent_payments = staff_member.received_payments.select_related(
        'order__customer'
    ).order_by('-payment_date')[:10]
    
    context = {
        'staff_member': staff_member,
        'stats': stats,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'accounts/staff_detail.html', context)


@login_required
def staff_edit(request, pk):
    """
    Texnik xodimni tahrirlash
    """
    staff_member = get_object_or_404(User, pk=pk, role='technician')
    
    # Faqat menejer va admin tahrirlaya oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda texnik xodimni tahrirlash huquqi yo\'q!')
        return redirect('staff:detail', pk=pk)
    
    if request.method == 'POST':
        form = TechnicianEditForm(request.POST, instance=staff_member)
        if form.is_valid():
            staff_member = form.save()
            messages.success(
                request, 
                f'{staff_member.get_full_name() or staff_member.username} ma\'lumotlari yangilandi!'
            )
            return redirect('staff:detail', pk=staff_member.pk)
    else:
        form = TechnicianEditForm(instance=staff_member)
    
    context = {
        'form': form,
        'staff_member': staff_member,
        'title': f'{staff_member.get_full_name() or staff_member.username} ma\'lumotlarini tahrirlash',
    }
    
    return render(request, 'accounts/staff_form.html', context)


@login_required
def staff_reset_password(request, pk):
    """
    Texnik xodim parolini yangilash
    """
    staff_member = get_object_or_404(User, pk=pk, role='technician')
    
    # Faqat menejer va admin parol o'zgartira oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda parol o\'zgartirish huquqi yo\'q!')
        return redirect('staff:detail', pk=pk)
    
    if request.method == 'POST':
        form = StaffPasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            staff_member.set_password(new_password)
            staff_member.save()
            
            messages.success(
                request, 
                f'{staff_member.get_full_name() or staff_member.username} paroli yangilandi!'
            )
            return redirect('staff:detail', pk=staff_member.pk)
    else:
        form = StaffPasswordResetForm()
    
    context = {
        'form': form,
        'staff_member': staff_member,
        'title': f'{staff_member.get_full_name() or staff_member.username} parolini yangilash',
    }
    
    return render(request, 'accounts/password_reset.html', context)


@login_required
def staff_toggle_status(request, pk):
    """
    Texnik xodimni faollashtirish/o'chirish
    """
    staff_member = get_object_or_404(User, pk=pk, role='technician')
    
    # Faqat admin status o'zgartira oladi
    if not request.user.is_admin():
        messages.error(request, 'Sizda xodim statusini o\'zgartirish huquqi yo\'q!')
        return redirect('staff:detail', pk=pk)
    
    if request.method == 'POST':
        staff_member.is_active = not staff_member.is_active
        staff_member.save()
        
        status_text = 'faollashtirildi' if staff_member.is_active else 'o\'chirildi'
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
    staff_member = get_object_or_404(User, pk=pk, role='technician')
    
    # Faqat admin o'chira oladi
    if not request.user.is_admin():
        messages.error(request, 'Sizda xodimni o\'chirish huquqi yo\'q!')
        return redirect('staff:detail', pk=pk)
    
    # Buyurtmalari bo'lgan xodimni o'chirish mumkin emas
    if staff_member.created_orders.exists():
        messages.error(
            request, 
            'Bu xodimning buyurtmalari mavjud. Avval buyurtmalarni boshqa xodimlarga o\'tkazing!'
        )
        return redirect('staff:detail', pk=pk)
    
    if request.method == 'POST':
        staff_name = staff_member.get_full_name() or staff_member.username
        staff_member.delete()
        messages.success(request, f'Texnik xodim {staff_name} o\'chirildi!')
        return redirect('staff:list')
    
    context = {
        'staff_member': staff_member,
    }
    
    return render(request, 'accounts/staff_delete.html', context)