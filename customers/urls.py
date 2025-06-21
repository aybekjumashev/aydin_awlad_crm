# customers/urls.py - YANGILANGAN VERSIYA

from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # Asosiy mijozlar sahifalari
    path('', views.customer_list, name='list'),
    path('add/', views.customer_add, name='add'),
    path('<int:pk>/', views.customer_detail, name='detail'),
    path('<int:pk>/edit/', views.customer_edit, name='edit'),
    path('<int:pk>/delete/', views.customer_delete, name='delete'),
    
    # Telefon raqamlar bilan ishlash (AJAX)
    path('<int:customer_pk>/add-phone/', views.add_customer_phone, name='add_phone'),
    path('phone/<int:phone_pk>/delete/', views.delete_customer_phone, name='delete_phone'),
    
    # Eslatmalar
    path('<int:customer_pk>/add-note/', views.add_customer_note, name='add_note'),
    
    # AJAX va qidiruv
    path('ajax/search/', views.ajax_search_customers, name='ajax_search'),
    
    # Public sahifalar
    path('public/<uuid:uuid>/', views.public_customer_detail, name='public_detail'),
    path('quick-order/', views.quick_order, name='quick_order'),
]