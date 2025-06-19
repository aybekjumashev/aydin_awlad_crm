# customers/urls.py

from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # Authenticated views (login kerak)
    path('', views.customer_list, name='list'),
    path('<int:pk>/', views.customer_detail, name='detail'),
    path('add/', views.customer_add, name='add'),
    path('<int:pk>/edit/', views.customer_edit, name='edit'),
    path('<int:pk>/delete/', views.customer_delete, name='delete'),
    
    # AJAX endpoints
    path('ajax/search/', views.ajax_search_customers, name='ajax_search'),
    
    # Public views (login kerak emas) - oddiy versiya
    path('public/<int:uuid>/', views.public_customer_detail, name='public_detail'),
    path('quick-order/', views.quick_order, name='quick_order'),
]