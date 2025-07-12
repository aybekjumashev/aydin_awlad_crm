# telegram_bot/views.py

import json
import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from customers.models import Customer
from orders.models import Order
from .bot import bot, notify_new_order
from .forms import TelegramCustomerForm, TelegramOrderForm


# ================================
# WEBHOOK MANAGEMENT VIEWS (Admin only)
# ================================

@staff_member_required
def set_webhook(request):
    """Set Telegram webhook URL"""
    webhook_url = f"{settings.TELEGRAM_WEBHOOK_BASE_URL}/telegram/webhook/"
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
    data = {'url': webhook_url}
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        
        if result.get('ok'):
            messages.success(request, f'Webhook successfully set to: {webhook_url}')
        else:
            messages.error(request, f'Failed to set webhook: {result.get("description", "Unknown error")}')
    except Exception as e:
        messages.error(request, f'Error setting webhook: {str(e)}')
    
    return redirect('admin:index')


@staff_member_required
def delete_webhook(request):
    """Delete Telegram webhook"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteWebhook"
    
    try:
        response = requests.post(url)
        result = response.json()
        
        if result.get('ok'):
            messages.success(request, 'Webhook successfully deleted')
        else:
            messages.error(request, f'Failed to delete webhook: {result.get("description", "Unknown error")}')
    except Exception as e:
        messages.error(request, f'Error deleting webhook: {str(e)}')
    
    return redirect('admin:index')


@staff_member_required
def get_webhook_info(request):
    """Get current webhook information"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        if result.get('ok'):
            webhook_info = result.get('result', {})
            return JsonResponse({
                'success': True,
                'webhook_info': webhook_info
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('description', 'Unknown error')
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ================================
# PUBLIC CUSTOMER VIEWS (No Auth Required)
# ================================

def telegram_customer_public(request):
    """
    Public customer page accessible via Telegram bot
    URL: /public/customer/?tgid=12345678
    """
    telegram_id = request.GET.get('tgid')
    
    if not telegram_id:
        return render(request, 'telegram_bot/error.html', {
            'error_message': 'Telegram ID topilmadi. Botdan qayta kirish kerak.',
            'error_code': 'NO_TELEGRAM_ID'
        })
    
    # Find customer by telegram_id
    customer = Customer.get_by_telegram_id(telegram_id)
    
    if not customer:
        # Customer not found, redirect to registration
        return redirect(f'/public/customer/register/?tgid={telegram_id}')
    
    # Check if customer profile is complete
    if not customer.is_complete_profile():
        return redirect(f'/public/customer/register/?tgid={telegram_id}')
    
    # Get customer orders
    orders = customer.orders.all().order_by('-created_at')[:10]
    
    # Handle new order creation (SODDALASHTIRILGAN)
    if request.method == 'POST':
        order_form = TelegramOrderForm(request.POST, customer=customer)
        if order_form.is_valid():
            # Get form data
            measurement_address = order_form.cleaned_data.get('measurement_address', '').strip()
            notes = order_form.cleaned_data.get('notes', '').strip()
            
            # Use customer address if measurement address is empty
            final_address = measurement_address if measurement_address else customer.address
            
            try:
                # Create new order (FAQAT ORDER, ITEM YO'Q)
                order = Order.objects.create(
                    customer=customer,
                    status='measuring',  # Start with measuring status
                    address=final_address,
                    notes=notes
                )
                
                # Generate order number if not auto-generated
                if not order.order_number:
                    order.order_number = f"ORD-{order.id:06d}"
                    order.save()
                
                # Send notification
                try:
                    notify_new_order(customer, order)
                except Exception as e:
                    # Log error but don't fail the order creation
                    print(f"Notification error: {e}")
                
                messages.success(request, 'Buyurtma muvaffaqiyatli qabul qilindi! Xodimlarimiz tez orada siz bilan bog\'lanishadi.')
                return redirect(f'/public/customer/?tgid={telegram_id}')
                
            except Exception as e:
                messages.error(request, f'Buyurtma yaratishda xatolik: {str(e)}')
        else:
            messages.error(request, 'Forma ma\'lumotlarini tekshiring.')
    else:
        order_form = TelegramOrderForm(customer=customer)
    
    context = {
        'customer': customer,
        'orders': orders,
        'order_form': order_form,
        'telegram_id': telegram_id,
        'is_telegram_view': True,
    }
    
    return render(request, 'telegram_bot/customer_dashboard.html', context)


def telegram_customer_register(request):
    """
    Customer registration form for Telegram users
    URL: /public/customer/register/?tgid=12345678
    """
    telegram_id = request.GET.get('tgid')
    
    if not telegram_id:
        return render(request, 'telegram_bot/error.html', {
            'error_message': 'Telegram ID topilmadi. Botdan qayta kirish kerak.',
            'error_code': 'NO_TELEGRAM_ID'
        })
    
    # Try to find existing customer
    customer = Customer.get_by_telegram_id(telegram_id)
    
    if request.method == 'POST':
        form = TelegramCustomerForm(request.POST, instance=customer)
        if form.is_valid():
            try:
                customer = form.save(commit=False)
                if not customer.telegram_id:
                    customer.telegram_id = telegram_id
                customer.save()
                
                messages.success(request, 'Ma\'lumotlar muvaffaqiyatli saqlandi!')
                return redirect(f'/public/customer/?tgid={telegram_id}')
            except Exception as e:
                messages.error(request, f'Ma\'lumotlar saqlanmadi: {str(e)}')
        else:
            messages.error(request, 'Forma ma\'lumotlarini tekshiring.')
    else:
        form = TelegramCustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'telegram_id': telegram_id,
        'is_telegram_view': True,
    }
    
    return render(request, 'telegram_bot/customer_register.html', context)


@csrf_exempt
def telegram_order_create(request):
    """
    AJAX endpoint for creating orders via Telegram interface
    SODDALASHTIRILGAN - faqat order yaratish, item yo'q
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    telegram_id = request.POST.get('telegram_id')
    if not telegram_id:
        return JsonResponse({'success': False, 'error': 'Telegram ID required'})
    
    customer = Customer.get_by_telegram_id(telegram_id)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer not found'})
    
    try:
        # Get form data
        measurement_address = request.POST.get('measurement_address', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Use customer address if measurement address is empty
        final_address = measurement_address if measurement_address else customer.address
        
        # Create order (FAQAT ORDER)
        order = Order.objects.create(
            customer=customer,
            status='measuring',  # Start with measuring status
            address=final_address,
            notes=notes
        )
        
        # Generate order number if not auto-generated
        if not order.order_number:
            order.order_number = f"ORD-{order.id:06d}"
            order.save()
        
        # Send notification
        try:
            notify_new_order(customer, order)
        except Exception as e:
            # Log error but don't fail the order creation
            print(f"Notification error: {e}")
        
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'message': 'Buyurtma muvaffaqiyatli yaratildi! Xodimlarimiz tez orada siz bilan bog\'lanishadi.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Buyurtma yaratishda xatolik: {str(e)}'
        })


# ================================
# HELPER FUNCTIONS
# ================================

def get_order_status_display(status):
    """Get user-friendly status display"""
    status_map = {
        'measuring': '📏 O\'lchov olinmoqda',
        'processing': '🔧 Ishlab chiqarilmoqda',
        'installing': '🚚 O\'rnatilmoqda',
        'installed': '✅ O\'rnatildi',
        'cancelled': '❌ Bekor qilindi'
    }
    return status_map.get(status, status)