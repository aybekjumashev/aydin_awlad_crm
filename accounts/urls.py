# accounts/urls.py - TUZATILGAN VERSIYA

from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifalar
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile (views.py da mavjud funksiyani ishlatamiz)
    path('profile/', views.profile, name='profile'),
    
    # Parol o'zgartirish
    path('change-password/', views.change_password, name='change_password'),
    
    # AJAX endpoints
    path('ajax/dashboard-stats/', views.get_dashboard_stats, name='dashboard_stats'),
]