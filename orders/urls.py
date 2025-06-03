# orders/urls.py

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='list'),
    path('add/', views.order_add, name='add'),
    path('<int:pk>/', views.order_detail, name='detail'),
    path('<int:pk>/edit/', views.order_edit, name='edit'),
    path('<int:pk>/delete/', views.order_delete, name='delete'),
    path('<int:pk>/status/', views.order_status_update, name='status_update'),
    path('<int:pk>/add-item/', views.order_add_item, name='add_item'),
    path('<int:pk>/print/', views.order_print, name='print'),
]