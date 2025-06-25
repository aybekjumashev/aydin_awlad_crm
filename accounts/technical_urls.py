# accounts/technical_urls.py
from django.urls import path
from . import technical_views

app_name = 'technical'

urlpatterns = [
    # Dashboard
    path('dashboard/', technical_views.technical_dashboard, name='dashboard'),
    
    # Vazifalar
    path('my-tasks/', technical_views.my_tasks, name='my_tasks'),
    
    # O'lchov olish
    path('measurement/<int:order_id>/', technical_views.measurement_form, name='measurement'),
    
    # Ishlab chiqarish
    path('manufacturing/<int:order_id>/', technical_views.manufacturing_task, name='manufacturing'),
    
    # O'rnatish
    path('installation/<int:order_id>/', technical_views.installation_task, name='installation'),
]