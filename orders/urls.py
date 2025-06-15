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
    path('<int:pk>/items/add/', views.order_item_add, name='item_add'),
    path('items/<int:pk>/edit/', views.order_item_edit, name='item_edit'),
    path('items/<int:pk>/delete/', views.order_item_delete, name='item_delete'),
    path('<int:pk>/pdf/', views.order_pdf, name='pdf'),
    path('ajax/stats/', views.order_ajax_stats, name='ajax_stats'),
]