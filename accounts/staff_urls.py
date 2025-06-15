# accounts/staff_urls.py - QAYTA YARATILGAN

from django.urls import path
from . import staff_views

app_name = 'staff'

urlpatterns = [
    path('', staff_views.staff_list, name='list'),
    path('add/', staff_views.staff_add, name='add'),
    path('<int:pk>/', staff_views.staff_detail, name='detail'),
    path('<int:pk>/edit/', staff_views.staff_edit, name='edit'),
    path('<int:pk>/reset-password/', staff_views.staff_reset_password, name='reset_password'),
    path('<int:pk>/toggle-status/', staff_views.staff_toggle_status, name='toggle_status'),
    path('<int:pk>/delete/', staff_views.staff_delete, name='delete'),
]