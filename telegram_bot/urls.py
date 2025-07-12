# telegram_bot/urls.py

from django.urls import path
from . import views
from .bot import TelegramWebhookView

app_name = 'telegram_bot'

urlpatterns = [
    # Webhook endpoint
    path('webhook/', TelegramWebhookView.as_view(), name='webhook'),
    
    # Bot management views (admin only)
    path('set-webhook/', views.set_webhook, name='set_webhook'),
    path('delete-webhook/', views.delete_webhook, name='delete_webhook'),
    path('get-webhook-info/', views.get_webhook_info, name='get_webhook_info'),
]

# Public URLs (separate patterns for cleaner organization)
public_urlpatterns = [
    path('public/customer/', views.telegram_customer_public, name='customer_public'),
    path('public/customer/register/', views.telegram_customer_register, name='customer_register'),
    path('public/order/create/', views.telegram_order_create, name='order_create'),
]

# Combine all patterns
urlpatterns += public_urlpatterns