# customers/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Customer
from .forms import CustomerForm


@login_required
def customer_list(request):
    """
    Mijozlar ro'yxati
    """
    # Faqat menejer va admin ko'ra oladi
    if not (request.user.is_manager() or request.user.is_admin() or request.user.is_technician()):
        messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
        return redirect('dashboard')
    
    customers = Customer.objects.all()
    
    # Qidiruv
    search = request.GET.get('search')
    if search:
        customers = customers.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(address__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    customers = paginator.get_page(page_number)
    
    context = {
        'customers': customers,
        'search': search,
    }
    
    return render(request, 'customers/list.html', context)


@login_required
def customer_detail(request, pk):
    """
    Mijoz tafsilotlari
    """
    customer = get_object_or_404(Customer, pk=pk)
    
    # Mijozning buyurtmalari
    orders = customer.orders.all().order_by('-created_at')
    
    context = {
        'customer': customer,
        'orders': orders,
    }
    
    return render(request, 'customers/detail.html', context)


@login_required
def customer_add(request):
    """
    Yangi mijoz qo'shish
    """
    # Faqat menejer va admin qo'sha oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda mijoz qo\'shish huquqi yo\'q!')
        return redirect('dashboard')
    
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


@login_required
def customer_edit(request, pk):
    """
    Mijoz ma'lumotlarini tahrirlash
    """
    customer = get_object_or_404(Customer, pk=pk)
    
    # Faqat menejer va admin tahrirlaya oladi
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, 'Sizda mijoz ma\'lumotlarini tahrirlash huquqi yo\'q!')
        return redirect('customers:detail', pk=pk)
    
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


@login_required
def customer_delete(request, pk):
    """
    Mijozni o'chirish
    """
    customer = get_object_or_404(Customer, pk=pk)
    
    # Faqat admin o'chira oladi
    if not request.user.is_admin():
        messages.error(request, 'Sizda mijozni o\'chirish huquqi yo\'q!')
        return redirect('customers:detail', pk=pk)
    
    # Buyurtmalari bor mijozni o'chirish mumkin emas
    if customer.orders.exists():
        messages.error(request, 'Bu mijozning buyurtmalari mavjud. Avval buyurtmalarni o\'chiring!')
        return redirect('customers:detail', pk=pk)
    
    if request.method == 'POST':
        customer_name = customer.get_full_name()
        customer.delete()
        messages.success(request, f'Mijoz {customer_name} o\'chirildi!')
        return redirect('customers:list')
    
    context = {
        'customer': customer,
    }
    
    return render(request, 'customers/delete.html', context)