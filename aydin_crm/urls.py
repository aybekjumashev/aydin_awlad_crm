# aydin_crm/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('customers/', include('customers.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    # path('reports/', include('reports.urls')),
]

# Media fayllar uchun (development muhitida)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin panel sarlavhalarini o'zgartirish
admin.site.site_header = "AYDIN AWLAD CRM"
admin.site.site_title = "AYDIN AWLAD"
admin.site.index_title = "Boshqaruv paneli"