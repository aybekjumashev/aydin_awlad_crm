# customers/views.py - TOZALANGAN VERSIYA

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse

from .models import Customer
from .forms import CustomerForm, CustomerSearchForm, PublicCustomerOrderForm, QuickOrderForm


@login_required
def customer_list(request):
    """
    Mijozlar ro'yxati
    """
    try:
        # Huquqlarni tekshirish
        if not (request.user.is_manager() or request.user.is_admin() or request.user.is_technician()):
            messages.error(request, 'Sizda bu sahifani ko\'rish huquqi yo\'q!')
            return redirect('admin:index')
        
        customers = Customer.objects.all()
        search_form = CustomerSearchForm(request.GET)
        
        # Qidiruv
        if search_form.is_valid():
            search = search_form.cleaned_data.get('search')
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
            'search_form': search_form,
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
            }
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
        if not (request.user.is_manager() or request.user.is_admin()):
            messages.error(request, 'Sizda mijoz qo\'shish huquqi yo\'q!')
            return redirect('admin:index')
        
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
        if not request.user.is_admin():
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


# PUBLIC SAHIFALAR (Login kerak emas)

def public_customer_detail(request, uuid):
    """
    Mijoz uchun public sahifa (UUID orqali)
    """
    try:
        customer = Customer.objects.get(pk=uuid)
        
        # Mijozning buyurtmalari
        orders = customer.orders.all().order_by('-created_at')
        
        # Agar POST so'rov bo'lsa, yangi buyurtma yaratish
        if request.method == 'POST':
            order_form = PublicCustomerOrderForm(request.POST)
            if order_form.is_valid():
                # Orders modelidan import
                from orders.models import Order, OrderItem
                
                # Yangi buyurtma yaratish
                order = Order.objects.create(
                    customer=customer,
                    status='measuring',
                    address=order_form.cleaned_data['address'],
                    notes=f"""
                    Mijoz tomonidan berilgan buyurtma:
                    - Telefon: {order_form.cleaned_data['phone']}
                    - Xona: {order_form.cleaned_data.get('room_name', 'Ko\'rsatilmagan')}
                    - Taxminiy o'lcham: {order_form.cleaned_data.get('approximate_size', 'Ko\'rsatilmagan')}
                    - Qulay vaqt: {order_form.cleaned_data.get('preferred_time', 'Ko\'rsatilmagan')}
                    - Izoh: {order_form.cleaned_data.get('notes', 'Yo\'q')}
                    """.strip()
                )
                
                # Buyurtma elementi yaratish
                OrderItem.objects.create(
                    order=order,
                    blind_type=order_form.cleaned_data['blind_type'],
                    width=100,  # Default qiymat
                    height=100,  # Default qiymat
                    material='aluminum',  # Default
                    installation_type='wall',  # Default
                    quantity=1,
                    unit_price=0  # Keyinchalik to'ldiriladi
                )
                
                messages.success(request, 'Buyurtmangiz qabul qilindi! Tez orada siz bilan bog\'lanamiz.')
                return redirect('customers:public_detail', uuid=uuid)
        else:
            order_form = PublicCustomerOrderForm()
        
        context = {
            'customer': customer,
            'orders': orders,
            'order_form': order_form,
        }
        
        return render(request, 'customers/public_detail.html', context)
    except Customer.DoesNotExist:
        return HttpResponse("Mijoz topilmadi")
    except Exception as e:
        return HttpResponse(f"Xatolik: {str(e)}")


def quick_order(request):
    """
    Tezkor buyurtma berish sahifasi (barcha uchun ochiq)
    """
    try:
        if request.method == 'POST':
            form = QuickOrderForm(request.POST)
            if form.is_valid():
                # Mijozni topish yoki yaratish
                customer_name_parts = form.cleaned_data['customer_name'].split()
                first_name = customer_name_parts[0] if customer_name_parts else 'Noma\'lum'
                last_name = ' '.join(customer_name_parts[1:]) if len(customer_name_parts) > 1 else ''
                
                customer, created = Customer.objects.get_or_create(
                    phone=form.cleaned_data['customer_phone'],
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'address': form.cleaned_data['address']
                    }
                )
                
                # Buyurtma yaratish
                from orders.models import Order, OrderItem
                
                order = Order.objects.create(
                    customer=customer,
                    status='measuring',
                    address=form.cleaned_data['address'],
                    notes=f"""
                    Tezkor buyurtma:
                    - Xonalar soni: {form.cleaned_data['room_count']}
                    - Taxminiy o'lcham: {form.cleaned_data.get('approximate_size', 'Ko\'rsatilmagan')}
                    - Qulay aloqa vaqti: {form.cleaned_data.get('preferred_contact_time', 'Ko\'rsatilmagan')}
                    - Qo'shimcha: {form.cleaned_data.get('notes', 'Yo\'q')}
                    """.strip()
                )
                
                # Buyurtma elementlari yaratish
                for i in range(form.cleaned_data['room_count']):
                    OrderItem.objects.create(
                        order=order,
                        blind_type=form.cleaned_data['blind_type'],
                        width=100,  # Default
                        height=100,  # Default
                        material='aluminum',  # Default
                        installation_type='wall',  # Default
                        quantity=1,
                        unit_price=0  # Keyinchalik to'ldiriladi
                    )
                
                messages.success(request, 
                    f'Buyurtmangiz #{order.order_number} qabul qilindi! '
                    f'24 soat ichida siz bilan bog\'lanamiz.'
                )
                
                # Mijozning shaxsiy sahifasiga yo'naltirish
                return redirect('customers:public_detail', uuid=customer.pk)
        else:
            form = QuickOrderForm()
        
        context = {
            'form': form,
        }
        
        return render(request, 'customers/quick_order.html', context)
    except Exception as e:
        return HttpResponse(f"Xatolik: {str(e)}")


def ajax_search_customers(request):
    """
    AJAX mijozlarni qidirish
    """
    try:
        if request.method == 'GET':
            search = request.GET.get('q', '')
            customers = Customer.objects.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search)
            )[:10]
            
            results = []
            for customer in customers:
                results.append({
                    'id': customer.pk,
                    'name': customer.get_full_name(),
                    'phone': customer.phone,
                    'address': customer.address[:50] + '...' if len(customer.address) > 50 else customer.address
                })
            
            return JsonResponse({'customers': results})
        
        return JsonResponse({'error': 'Invalid request'})
    except Exception as e:
        return JsonResponse({'error': str(e)})