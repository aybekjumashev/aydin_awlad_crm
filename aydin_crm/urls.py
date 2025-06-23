# main_project/urls.py - YANGILANGAN VERSIYA

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('dashboard')),  # Asosiy sahifa
    path('accounts/', include('accounts.urls')),
    path('technical/', include('accounts.technical_urls')),  # YANGI: Texnik xodim URL'lari
    path('customers/', include('customers.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('staff/', include('accounts.staff_urls')),  # Staff boshqaruv URL'lari
]