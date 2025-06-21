# aydin_crm/urls.py - TUZATILGAN VERSIYA

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Asosiy accounts URL'lari
    path('', include('accounts.urls')),
    
    # Mijozlar
    path('customers/', include('customers.urls')),
    
    # Buyurtmalar
    path('orders/', include('orders.urls')),
    
    # To'lovlar
    path('payments/', include('payments.urls')),
    
    # Texnik xodimlar - ✅ BU QATORNI UNCOMMENT QILDIK
    path('technical/', include('accounts.technical_urls')),
    
    # Xodimlar boshqaruvi
    path('staff/', include('accounts.staff_urls')),
    
    # Hisobotlar (kelajakda qo'shiladi)
    # path('reports/', include('reports.urls')),
]

# Media fayllar uchun (development muhitida)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin panel sarlavhalarini o'zgartirish
admin.site.site_header = "AYDIN AWLAD CRM - Boshqaruv paneli"
admin.site.site_title = "AYDIN AWLAD CRM"
admin.site.index_title = "CRM tizimi boshqaruv paneli"