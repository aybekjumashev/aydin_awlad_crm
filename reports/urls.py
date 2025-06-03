# reports/urls.py

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard, name='dashboard'),
    path('customers/', views.customer_report, name='customers'),
    path('orders/', views.order_report, name='orders'),
    path('payments/', views.payment_report, name='payments'),
    path('financial/', views.financial_report, name='financial'),
]