# customers/views.py - FORM SUBMIT MUAMMOSI TUZATILGAN

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.forms import inlineformset_factory
from django.db import transaction
import traceback

from .models import Customer, CustomerPhone, CustomerNote
from .forms import CustomerForm, CustomerPhoneForm, CustomerNoteForm


@login_required
def customer_list(request):
    """
    Mijozlar ro'yxati
    """
    try:
        # Huquqlarni tekshirish
        if not (request.user.is_manager or request.user.is_admin or request.user.is_technical):
            messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
            return redirect('dashboard')
        
        customers = Customer.objects.all()
        
        # Qidiruv
        search = request.GET.get('search', '')
        if search:
            customers = customers.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(address__icontains=search) |
                Q(additional_phones__phone_number__icontains=search)
            ).distinct()
        
        # Kategoriya bo'yicha filtr
        category = request.GET.get('category', '')
        if category:
            customers = customers.filter(category=category)
        
        # Pagination
        paginator = Paginator(customers.order_by('-created_at'), 20)
        page_number = request.GET.get('page')
        customers = paginator.get_page(page_number)
        
        context = {
            'customers': customers,
            'search': search,
            'category': category,
            'category_choices': Customer.CATEGORY_CHOICES,
            'title': 'Mijozlar ro\'yxati'
        }
        
        return render(request, 'customers/list.html', context)
    except Exception as e:
        messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        return redirect('dashboard')


@login_required
def customer_detail(request, pk):
    """
    Mijoz tafsilotlari
    """
    try:
        customer = get_object_or_404(Customer, pk=pk)
        
        # Mijozning buyurtmalari
        orders = customer.orders.all().order_by('-created_at')
        
        # Qo'shimcha telefon raqamlar
        additional_phones = customer.additional_phones.all().order_by('-is_primary', '-created_at')
        
        # Eslatmalar
        notes = customer.customer_notes.all().order_by('-created_at')
        
        # Statistika
        total_orders = orders.count()
        completed_orders = orders.filter(status='installed').count()
        active_orders = orders.exclude(status__in=['cancelled', 'installed']).count()
        
        context = {
            'customer': customer,
            'recent_orders': orders,
            'additional_phones': additional_phones,
            'notes': notes,
            'stats': {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'active_orders': active_orders,
            },
            'title': f'{customer.get_full_name()} - Tafsilotlar'
        }
        
        return render(request, 'customers/detail.html', context)
    except Exception as e:
        messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        return redirect('customers:list')


@login_required
def customer_add(request):
    """
    Yangi mijoz qo'shish - ODDIY VERSIYA (formset ishlatsiz)
    """
    try:
        # Huquqlarni tekshirish
        if not (request.user.is_manager or request.user.is_admin):
            messages.error(request, 'Sizda mijoz qo\'shish huquqi yo\'q!')
            return redirect('customers:list')
        
        if request.method == 'POST':
            print("POST ma'lumotlari:", request.POST)  # Debug uchun
            
            form = CustomerForm(request.POST)
            
            if form.is_valid():
                print("Form valud!")  # Debug uchun
                try:
                    customer = form.save(commit=False)
                    customer.created_by = request.user
                    customer.save()
                    
                    messages.success(
                        request, 
                        f'Mijoz {customer.get_full_name()} muvaffaqiyatli qo\'shildi!'
                    )
                    return redirect('customers:detail', pk=customer.pk)
                except Exception as save_error:
                    print(f"Saqlashda xatolik: {save_error}")
                    messages.error(request, f'Saqlashda xatolik: {str(save_error)}')
            else:
                print("Form xatoliklari:", form.errors)  # Debug uchun
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            form = CustomerForm()
        
        context = {
            'form': form,
            'title': 'Yangi mijoz qo\'shish',
            'is_edit': False,
        }
        
        return render(request, 'customers/form_simple.html', context)
        
    except Exception as e:
        print(f"Umumiy xatolik: {e}")
        print(traceback.format_exc())
        messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        return redirect('customers:list')


@login_required
def customer_edit(request, pk):
    """
    Mijoz ma'lumotlarini tahrirlash - ODDIY VERSIYA
    """
    try:
        customer = get_object_or_404(Customer, pk=pk)
        
        # Huquqlarni tekshirish
        if not (request.user.is_manager or request.user.is_admin):
            messages.error(request, 'Sizda mijoz ma\'lumotlarini tahrirlash huquqi yo\'q!')
            return redirect('customers:detail', pk=pk)
        
        if request.method == 'POST':
            print("POST ma'lumotlari:", request.POST)  # Debug uchun
            
            form = CustomerForm(request.POST, instance=customer)
            
            if form.is_valid():
                print("Form valid!")  # Debug uchun
                try:
                    customer = form.save()
                    
                    messages.success(
                        request, 
                        f'Mijoz {customer.get_full_name()} ma\'lumotlari yangilandi!'
                    )
                    return redirect('customers:detail', pk=customer.pk)
                except Exception as save_error:
                    print(f"Saqlashda xatolik: {save_error}")
                    messages.error(request, f'Saqlashda xatolik: {str(save_error)}')
            else:
                print("Form xatoliklari:", form.errors)  # Debug uchun
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            form = CustomerForm(instance=customer)
        
        context = {
            'form': form,
            'customer': customer,
            'title': f'{customer.get_full_name()} ma\'lumotlarini tahrirlash',
            'is_edit': True,
        }
        
        return render(request, 'customers/form_simple.html', context)
        
    except Exception as e:
        print(f"Umumiy xatolik: {e}")
        print(traceback.format_exc())
        messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        return redirect('customers:detail', pk=pk)


@login_required
def customer_delete(request, pk):
    """
    Mijozni o'chirish
    """
    try:
        customer = get_object_or_404(Customer, pk=pk)
        
        # Faqat admin o'chira oladi
        if not request.user.is_admin:
            messages.error(request, 'Sizda mijozni o\'chirish huquqi yo\'q!')
            return redirect('customers:detail', pk=pk)
        
        if request.method == 'POST':
            customer_name = customer.get_full_name()
            customer.delete()
            messages.success(request, f'Mijoz {customer_name} o\'chirildi!')
            return redirect('customers:list')
        
        context = {
            'customer': customer,
            'orders_count': customer.orders.count(),
            'phones_count': customer.additional_phones.count(),
        }
        
        return render(request, 'customers/delete.html', context)
    except Exception as e:
        messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        return redirect('customers:detail', pk=pk)


@login_required
def add_customer_phone(request, customer_pk):
    """
    Mijozga qo'shimcha telefon qo'shish (AJAX)
    """
    try:
        customer = get_object_or_404(Customer, pk=customer_pk)
        
        if not (request.user.is_manager or request.user.is_admin):
            return JsonResponse({'success': False, 'error': 'Huquq yo\'q'})
        
        if request.method == 'POST':
            form = CustomerPhoneForm(request.POST)
            if form.is_valid():
                phone = form.save(commit=False)
                phone.customer = customer
                phone.save()
                
                return JsonResponse({
                    'success': True,
                    'phone_id': phone.pk,
                    'phone_number': phone.phone_number,
                    'phone_type': phone.get_phone_type_display(),
                    'is_primary': phone.is_primary
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        
        return JsonResponse({'success': False, 'error': 'POST so\'rov kerak'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_customer_phone(request, phone_pk):
    """
    Mijoz telefon raqamini o'chirish (AJAX)
    """
    try:
        phone = get_object_or_404(CustomerPhone, pk=phone_pk)
        
        if not (request.user.is_manager or request.user.is_admin):
            return JsonResponse({'success': False, 'error': 'Huquq yo\'q'})
        
        if request.method == 'POST':
            phone.delete()
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'POST so\'rov kerak'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def add_customer_note(request, customer_pk):
    """
    Mijozga eslatma qo'shish
    """
    try:
        customer = get_object_or_404(Customer, pk=customer_pk)
        
        if request.method == 'POST':
            form = CustomerNoteForm(request.POST)
            if form.is_valid():
                note = form.save(commit=False)
                note.customer = customer
                note.created_by = request.user
                note.save()
                
                messages.success(request, 'Eslatma qo\'shildi!')
                return redirect('customers:detail', pk=customer.pk)
        
        return redirect('customers:detail', pk=customer.pk)
    except Exception as e:
        messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        return redirect('customers:detail', pk=customer_pk)


# AJAX va PUBLIC sahifalar

@login_required
def ajax_search_customers(request):
    """
    AJAX orqali mijozlarni qidirish
    """
    search = request.GET.get('q', '')
    customers = []
    
    if search:
        customer_list = Customer.objects.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(additional_phones__phone_number__icontains=search)
        ).distinct()[:10]
        
        customers = [{
            'id': customer.pk,
            'text': f"{customer.get_full_name()} - {customer.phone}",
            'name': customer.get_full_name(),
            'phone': customer.phone,
            'address': customer.address
        } for customer in customer_list]
    
    return JsonResponse({'results': customers})


def public_customer_detail(request, uuid):
    """
    Mijoz uchun public sahifa
    """
    try:
        customer = get_object_or_404(Customer, public_uuid=uuid)
        
        # Mijozning buyurtmalari (faqat asosiy ma'lumotlar)
        orders = customer.orders.exclude(status='cancelled').order_by('-created_at')
        
        context = {
            'customer': customer,
            'orders': orders
        }
        
        return render(request, 'customers/public_detail.html', context)
    except Exception as e:
        return HttpResponse(f"Mijoz topilmadi: {str(e)}")


def quick_order(request):
    """
    Tezkor buyurtma
    """
    if request.method == 'POST':
        # Bu yerda tezkor buyurtma logikasi bo'lishi kerak
        messages.success(request, 'Buyurtmangiz qabul qilindi!')
        return redirect('customers:list')
    
    return render(request, 'customers/quick_order.html')