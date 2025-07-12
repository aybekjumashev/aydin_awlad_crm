# aydin_crm/urls.py - FIXED TELEGRAM BOT URLS

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from telegram_bot import views as telegram_views

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Main dashboard redirect
    path('', lambda request: redirect('dashboard')),
    
    # Core app URLs
    path('accounts/', include('accounts.urls')),
    path('technical/', include('accounts.technical_urls')),
    path('customers/', include('customers.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('staff/', include('accounts.staff_urls')),
    
    # Telegram Bot URLs (webhook and admin functions)
    path('telegram/', include('telegram_bot.urls')),
    
    # Direct public access URLs (for cleaner Telegram Web App URLs)
    path('public/customer/', telegram_views.telegram_customer_public, name='public_customer'),
    path('public/customer/register/', telegram_views.telegram_customer_register, name='public_customer_register'),
    path('public/order/create/', telegram_views.telegram_order_create, name='public_order_create'),
]

# Static and media files serving (for development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)