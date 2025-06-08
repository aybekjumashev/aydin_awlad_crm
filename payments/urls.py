# payments/urls.py faylini yaratish kerak:

# payments/urls.py

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='list'),
    path('add/<int:order_pk>/', views.payment_add, name='add'),
    path('<int:pk>/edit/', views.payment_edit, name='edit'),
    path('<int:pk>/delete/', views.payment_delete, name='delete'),
    path('daily-report/', views.daily_payment_report, name='daily_report'),
]