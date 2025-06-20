# accounts/decorators.py - YANGI FAYL

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def role_required(allowed_roles):
    """
    Foydalanuvchi rolini tekshiruvchi decorator
    
    Usage:
    @role_required(['admin', 'manager'])
    def my_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request, 
                    'Bu sahifani ko\'rish uchun sizda yetarli huquq yo\'q'
                )
                return redirect('dashboard')
        return _wrapped_view
    return decorator


def permission_required(permission_name):
    """
    Maxsus huquqni tekshiruvchi decorator
    
    Usage:
    @permission_required('can_measure')
    def measurement_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if hasattr(request.user, permission_name) and getattr(request.user, permission_name):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request,
                    f'Bu amalni bajarish uchun "{permission_name}" huquqi kerak'
                )
                return redirect('dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """
    Faqat admin uchun decorator
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_admin:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Bu sahifa faqat adminlar uchun')
            return redirect('dashboard')
    return _wrapped_view


def manager_required(view_func):
    """
    Menejer yoki admin uchun decorator
    """
    @wraps(view_func)
    @login_required  
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_admin or request.user.is_manager:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Bu sahifa faqat menejerlar uchun')
            return redirect('dashboard')
    return _wrapped_view


def technical_required(view_func):
    """
    Texnik xodim uchun decorator
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_technical:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Bu sahifa faqat texnik xodimlar uchun')
            return redirect('dashboard')
    return _wrapped_view


def can_create_order(view_func):
    """
    Buyurtma yaratish huquqini tekshiruvchi decorator
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if (request.user.is_admin or 
            request.user.is_manager or 
            request.user.can_create_order):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Buyurtma yaratish huquqingiz yo\'q')
            return redirect('orders:list')
    return _wrapped_view


def can_manage_payments(view_func):
    """
    To'lovlarni boshqarish huquqini tekshiruvchi decorator
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if (request.user.is_admin or 
            request.user.is_manager or 
            request.user.can_manage_payments):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'To\'lovlarni boshqarish huquqingiz yo\'q')
            return redirect('dashboard')
    return _wrapped_view