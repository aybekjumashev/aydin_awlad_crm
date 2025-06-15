# reports/urls.py

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard, name='dashboard'),
    path('customers/', views.customer_report, name='customers'),  # ✅ customer_reports → customer_report
    path('orders/', views.order_report, name='orders'),           # ✅ order_reports → order_report  
    path('payments/', views.payment_report, name='payments'),     # ✅ payment_reports → payment_report
    path('financial/', views.financial_report, name='financial'), # ✅ Bu mavjud
]