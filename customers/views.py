# customers/views.py - TO'LIQ TUZATILGAN VERSIYA

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse

from .models import Customer


@login_required
def customer_list(request):
    """
    Mijozlar ro'yxati
    """
    try:
        # Huquqlarni tekshirish - property lar method emas
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
                Q(address__icontains=search)
            ).distinct()
        
        # Pagination
        paginator = Paginator(customers.order_by('-created_at'), 20)
        page_number = request.GET.get('page')
        customers = paginator.get_page(page_number)
        
        context = {
            'customers': customers,
            'search': search,
            'title': 'Mijozlar ro\'yxati'
        }
        
        return render(request, 'customers/list.html', context)
    except Exception as e:
        return HttpResponse(f"Xatolik: {str(e)}")


@login_required
def customer_detail(request, pk):
    """
    Mijoz tafsilotlari
    """
    try:
        customer = get_object_or_404(Customer, pk=pk)
        
        # Mijozning buyurtmalari
        orders = customer.orders.all().order_by('-created_at')
        
        # Statistika
        total_orders = orders.count()
        completed_orders = orders.filter(status='installed').count()
        
        context = {
            'customer': customer,
            'orders': orders,
            'stats': {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
            },
            'title': f'{customer.get_full_name()} - Tafsilotlar'
        }
        
        return render(request, 'customers/detail.html', context)
    except Exception as e:
        return HttpResponse(f"Xatolik: {str(e)}")


@login_required
def customer_add(request):
    """
    Yangi mijoz qo'shish
    """
    try:
        # Huquqlarni tekshirish
        if not (request.user.is_manager or request.user.is_admin):
            messages.error(request, 'Sizda mijoz qo\'shish huquqi yo\'q!')
            return redirect('customers:list')
        
        from .forms import CustomerForm
        
        if request.method == 'POST':
            form = CustomerForm(request.POST)
            if form.is_valid():
                customer = form.save()
                messages.success(request, f'Mijoz {customer.get_full_name()} muvaffaqiyatli qo\'shildi!')
                return redirect('customers:detail', pk=customer.pk)
        else:
            form = CustomerForm()
        
        context = {
            'form': form,
            'title': 'Yangi mijoz qo\'shish',
        }
        
        return render(request, 'customers/form.html', context)
    except Exception as e:
        return HttpResponse(f"Xatolik: {str(e)}")


@login_required
def customer_edit(request, pk):
    """
    Mijoz ma'lumotlarini tahrirlash
    """
    try:
        customer = get_object_or_404(Customer, pk=pk)
        
        # Huquqlarni tekshirish
        if not (request.user.is_manager or request.user.is_admin):
            messages.error(request, 'Sizda mijoz ma\'lumotlarini tahrirlash huquqi yo\'q!')
            return redirect('customers:detail', pk=pk)
        
        from .forms import CustomerForm
        
        if request.method == 'POST':
            form = CustomerForm(request.POST, instance=customer)
            if form.is_valid():
                customer = form.save()
                messages.success(request, f'Mijoz {customer.get_full_name()} ma\'lumotlari yangilandi!')
                return redirect('customers:detail', pk=customer.pk)
        else:
            form = CustomerForm(instance=customer)
        
        context = {
            'form': form,
            'customer': customer,
            'title': f'{customer.get_full_name()} ma\'lumotlarini tahrirlash',
        }
        
        return render(request, 'customers/form.html', context)
    except Exception as e:
        return HttpResponse(f"Xatolik: {str(e)}")


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
        }
        
        return render(request, 'customers/delete.html', context)
    except Exception as e:
        return HttpResponse(f"Xatolik: {str(e)}")


# AJAX va PUBLIC sahifalar (oddiy versiya)

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
            Q(phone__icontains=search)
        )[:10]
        
        customers = [{
            'id': customer.pk,
            'text': f"{customer.get_full_name()} - {customer.phone}",
            'name': customer.get_full_name(),
            'phone': customer.phone
        } for customer in customer_list]
    
    return JsonResponse({'results': customers})


def public_customer_detail(request, uuid):
    """
    Mijoz uchun public sahifa (oddiy versiya)
    """
    try:
        customer = get_object_or_404(Customer, pk=uuid)
        
        # Mijozning buyurtmalari (faqat asosiy ma'lumotlar)
        orders = customer.orders.all().order_by('-created_at')
        
        context = {
            'customer': customer,
            'orders': orders
        }
        
        return render(request, 'customers/public_detail.html', context)
    except Exception as e:
        return HttpResponse(f"Mijoz topilmadi: {str(e)}")


def quick_order(request):
    """
    Tezkor buyurtma (oddiy versiya)
    """
    if request.method == 'POST':
        # Bu yerda tezkor buyurtma logikasi bo'lishi kerak
        # Hozircha oddiy message
        messages.success(request, 'Buyurtmangiz qabul qilindi!')
        return redirect('customers:list')
    
    return render(request, 'customers/quick_order.html')