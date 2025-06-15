# payments/urls.py

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='list'),
    path('add/', views.payment_add, name='add'),
    path('<int:order_pk>/add/', views.payment_add_to_order, name='add_to_order'),
    path('<int:pk>/', views.payment_detail, name='detail'),
    path('<int:pk>/edit/', views.payment_edit, name='edit'),
    path('<int:pk>/delete/', views.payment_delete, name='delete'),
    path('<int:pk>/confirm/', views.payment_confirm, name='confirm'),
    path('reports/', views.payment_reports, name='reports'),
    path('daily-report/', views.daily_payment_report, name='daily_report'),  # ✅ BU QATOR QO'SHILDI!
    path('ajax/order-info/', views.payment_ajax_order_info, name='ajax_order_info'),
]