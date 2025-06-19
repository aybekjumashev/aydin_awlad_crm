# orders/urls.py

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Asosiy buyurtma sahifalari
    path('', views.order_list, name='list'),
    path('<int:pk>/', views.order_detail, name='detail'),
    path('add/', views.order_add, name='add'),
    path('<int:pk>/edit/', views.order_edit, name='edit'),
    path('<int:pk>/delete/', views.order_delete, name='delete'),
]