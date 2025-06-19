# reports/urls.py - TO'G'IRLANGAN VERSIYA

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard, name='dashboard'),
    path('customers/', views.customers_report, name='customers'),     # ✅ To'g'irlandi
    path('orders/', views.orders_report, name='orders'),             # ✅ To'g'irlandi  
    path('payments/', views.payment_report, name='payments'),        # ✅ To'g'irlandi
    path('financial/', views.financial_report, name='financial'),    # ✅ Bu to'g'ri
]