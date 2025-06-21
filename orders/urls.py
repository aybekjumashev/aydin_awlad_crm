# orders/urls.py - ODDIY VA ISHLAYDIGNA VERSIYA

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Asosiy sahifalar
    path('', views.order_list, name='list'),
    path('create/', views.order_create, name='create'),
    path('<int:pk>/', views.order_detail, name='detail'),
    path('<int:pk>/edit/', views.order_edit, name='edit'),
    path('<int:pk>/delete/', views.order_delete, name='delete'),
    
    # Buyurtma jarayonlari
    path('<int:pk>/measurement/', views.order_measurement, name='measurement'),
    path('<int:pk>/status/', views.order_status_update, name='status_update'),
    path('<int:pk>/assign-staff/', views.order_assign_staff, name='assign_staff'),
    path('<int:pk>/print/', views.order_print, name='print'),
    
    # To'lovlar
    path('<int:pk>/add-payment/', views.order_add_payment, name='add_payment'),
    
    # AJAX endpoints
    path('api/stats/', views.get_order_stats, name='api_stats'),
    
    # Texnik xodim vazifalari
    path('my-tasks/', views.my_tasks, name='my_tasks'),
]