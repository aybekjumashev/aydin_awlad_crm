# telegram_bot/bot.py

import logging
import json
from typing import Dict, Any
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
import requests

from customers.models import Customer

# Logging setup
logger = logging.getLogger(__name__)

class TelegramBot:
    """
    AYDIN AWLAD Telegram bot main class
    """
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.base_url = settings.TELEGRAM_WEBHOOK_BASE_URL  # https://yourdomain.com
    
    def send_message(self, chat_id: int, text: str, reply_markup: Dict = None) -> Dict:
        """Send message to user"""
        url = f"{self.api_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {'ok': False, 'error': str(e)}
    
    def request_phone_number(self, chat_id: int) -> Dict:
        """Request phone number from user"""
        text = """
🏢 <b>AYDIN AWLAD jalyuzi o'rnatish xizmatiga xush kelibsiz!</b>

📱 Buyurtma berish uchun telefon raqamingizni ulashing.
        
👇 <b>"Telefon raqamni ulashish"</b> tugmasini bosing
        """
        
        keyboard = {
            'keyboard': [
                [
                    {
                        'text': '📱 Telefon raqamni ulashish',
                        'request_contact': True
                    }
                ]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': True
        }
        
        return self.send_message(chat_id, text, keyboard)
    
    def send_customer_web_app(self, chat_id: int, customer: Customer) -> Dict:
        """Send web app button to customer"""
        
        if customer.is_complete_profile():
            text = f"""
✅ <b>Assalomu alaykum, {customer.get_full_name()}!</b>

🛍 Buyurtmalaringizni ko'rish va yangi buyurtma berish uchun quyidagi tugmani bosing:
            """
            button_text = "🛍 Buyurtmalarni ko'rish"
        else:
            text = f"""
👋 <b>Assalomu alaykum!</b>

📝 Buyurtma berish uchun avval ma'lumotlaringizni to'ldiring:
            """
            button_text = "📝 Ma'lumotlarni to'ldirish"
        
        web_app_url = f"{self.base_url}/public/customer/?tgid={customer.telegram_id}"
        
        keyboard = {
            'inline_keyboard': [
                [
                    {
                        'text': button_text,
                        'web_app': {'url': web_app_url}
                    }
                ]
            ]
        }
        
        return self.send_message(chat_id, text, keyboard)
    
    def handle_start_command(self, chat_id: int, user_data: Dict) -> Dict:
        """Handle /start command"""
        # Check if customer already exists
        customer = Customer.get_by_telegram_id(chat_id)
        
        if customer:
            # Customer exists, send web app directly
            return self.send_customer_web_app(chat_id, customer)
        else:
            # New customer, request phone number
            return self.request_phone_number(chat_id)
    
    def handle_contact_received(self, chat_id: int, contact: Dict, user_data: Dict) -> Dict:
        """Handle when user shares contact"""
        phone_number = contact.get('phone_number', '')
        
        # Clean phone number format
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if not phone_number.startswith('998'):
            phone_number = '998' + phone_number.lstrip('0')
        
        phone_number = '+' + phone_number
        
        # Check if customer exists with this phone or telegram_id
        customer = Customer.get_by_telegram_id(chat_id)
        
        if not customer:
            # Try to find by phone number
            try:
                customer = Customer.objects.get(phone=phone_number)
                # Update with telegram_id
                customer.telegram_id = str(chat_id)
                customer.save()
            except Customer.DoesNotExist:
                # Create new customer
                first_name = user_data.get('first_name', '')
                last_name = user_data.get('last_name', '')
                
                customer = Customer.create_from_telegram(
                    telegram_id=chat_id,
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=last_name
                )
        
        # Send web app
        return self.send_customer_web_app(chat_id, customer)
    
    def handle_webhook_update(self, update_data: Dict) -> Dict:
        """Process incoming webhook update"""
        try:
            message = update_data.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            
            if not chat_id:
                return {'status': 'error', 'message': 'No chat_id found'}
            
            user_data = message.get('from', {})
            
            # Handle text messages
            if 'text' in message:
                text = message['text']
                
                if text == '/start':
                    result = self.handle_start_command(chat_id, user_data)
                    return {'status': 'success', 'result': result}
                else:
                    # Unknown command
                    self.send_message(
                        chat_id, 
                        "❓ Noma'lum buyruq. /start ni bosing."
                    )
                    return {'status': 'success', 'message': 'Unknown command handled'}
            
            # Handle contact sharing
            elif 'contact' in message:
                contact = message['contact']
                result = self.handle_contact_received(chat_id, contact, user_data)
                return {'status': 'success', 'result': result}
            
            else:
                # Unsupported message type
                self.send_message(
                    chat_id,
                    "🤖 Men faqat /start buyrug'i va telefon raqamni qabul qilaman."
                )
                return {'status': 'success', 'message': 'Unsupported message type'}
                
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {'status': 'error', 'message': str(e)}


# Bot instance
bot = TelegramBot()


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    """
    Telegram webhook handler view
    """
    
    def post(self, request):
        try:
            # Parse JSON data
            update_data = json.loads(request.body)
            
            # Log incoming update (for debugging)
            logger.info(f"Received webhook update: {update_data}")
            
            # Process update
            result = bot.handle_webhook_update(update_data)
            
            if result['status'] == 'success':
                return HttpResponse('OK')
            else:
                logger.error(f"Webhook processing failed: {result}")
                return HttpResponseBadRequest('Error processing update')
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request")
            return HttpResponseBadRequest('Invalid JSON')
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return HttpResponseBadRequest('Server error')
    
    def get(self, request):
        """For webhook verification"""
        return HttpResponse('Telegram Webhook is active!')


# Utility functions for notifications
def notify_new_order(customer, order):
    """Send notification about new order"""
    if customer.telegram_id:
        text = f"""
🎉 <b>Yangi buyurtma qabul qilindi!</b>

📋 Buyurtma raqami: #{order.order_number}
📅 Sana: {order.created_at.strftime('%d.%m.%Y %H:%M')}

Buyurtma tafsilotlarini ko'rish uchun quyidagi tugmani bosing:
        """
        
        keyboard = {
            'inline_keyboard': [
                [
                    {
                        'text': '📋 Buyurtmani ko\'rish',
                        'web_app': {
                            'url': f"{bot.base_url}/public/customer/?tgid={customer.telegram_id}"
                        }
                    }
                ]
            ]
        }
        
        bot.send_message(customer.telegram_id, text, keyboard)


def notify_status_change(customer, order, new_status):
    """Send notification about order status change"""
    if customer.telegram_id:
        status_messages = {
            'measuring': '📏 O\'lchov olinmoqda',
            'manufacturing': '🔧 Ishlab chiqarilmoqda',
            'installing': '🚚 O\'rnatilmoqda',
            'completed': '✅ Yakunlandi',
            'cancelled': '❌ Bekor qilindi'
        }
        
        status_text = status_messages.get(new_status, new_status)
        
        text = f"""
📢 <b>Buyurtma holati o'zgaridi!</b>

📋 Buyurtma: #{order.order_number}
🔄 Yangi holat: {status_text}
📅 Sana: {order.updated_at.strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = {
            'inline_keyboard': [
                [
                    {
                        'text': '📋 Buyurtmani ko\'rish',
                        'web_app': {
                            'url': f"{bot.base_url}/public/customer/?tgid={customer.telegram_id}"
                        }
                    }
                ]
            ]
        }
        
        bot.send_message(customer.telegram_id, text, keyboard)