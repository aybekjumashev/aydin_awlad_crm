# accounts/decorators.py - YANGI FAYL
# Texnik xodimlar uchun huquqlarni tekshirish decorator'lari

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Foydalanuvchi roli bo'yicha huquqni tekshirish
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            user_role = request.user.role
            if user_role not in allowed_roles:
                messages.error(
                    request, 
                    'Sizda bu sahifani ko\'rish huquqi yo\'q!'
                )
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """
    Faqat admin uchun
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_admin:
            messages.error(request, 'Faqat admin huquqiga ega foydalanuvchilar!')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def manager_required(view_func):
    """
    Menejer va admin uchun
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.is_manager or request.user.is_admin):
            messages.error(
                request, 
                'Faqat menejer va admin huquqiga ega foydalanuvchilar!'
            )
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def technical_required(view_func):
    """
    Texnik xodimlar uchun (o'z vazifalarini ko'rish)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_technical:
            messages.error(
                request, 
                'Bu sahifa faqat texnik xodimlar uchun!'
            )
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def can_create_order(view_func):
    """
    Buyurtma yaratish huquqi
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.can_create_order or 
                request.user.is_manager or 
                request.user.is_admin):
            messages.error(
                request, 
                'Sizda buyurtma yaratish huquqi yo\'q!'
            )
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def can_measure(view_func):
    """
    O'lchov olish huquqi
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.can_measure or 
                request.user.is_manager or 
                request.user.is_admin):
            messages.error(
                request, 
                'Sizda o\'lchov olish huquqi yo\'q!'
            )
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def can_manufacture(view_func):
    """
    Ishlab chiqarish huquqi
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.can_manufacture or 
                request.user.is_manager or 
                request.user.is_admin):
            messages.error(
                request, 
                'Sizda ishlab chiqarish huquqi yo\'q!'
            )
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def can_install(view_func):
    """
    O'rnatish huquqi
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.can_install or 
                request.user.is_manager or 
                request.user.is_admin):
            messages.error(
                request, 
                'Sizda o\'rnatish huquqi yo\'q!'
            )
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def can_manage_payments(view_func):
    """
    To'lovlarni boshqarish huquqi
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.can_manage_payments or 
                request.user.is_manager or 
                request.user.is_admin):
            messages.error(
                request, 
                'Sizda to\'lovlarni boshqarish huquqi yo\'q!'
            )
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def can_cancel_order(view_func):
    """
    Buyurtmani bekor qilish huquqi
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.can_cancel_order or 
                request.user.is_manager or 
                request.user.is_admin):
            messages.error(
                request, 
                'Sizda buyurtmani bekor qilish huquqi yo\'q!'
            )
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def permission_required_with_message(permission_check, error_message):
    """
    Umumiy huquq tekshirish decorator'i
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not permission_check(request.user):
                messages.error(request, error_message)
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# Maxsus huquqlar uchun yordamchi funksiyalar
def user_can_view_order(user, order):
    """
    Foydalanuvchi buyurtmani ko'ra oladimi?
    """
    if user.is_admin or user.is_manager:
        return True
    
    if user.is_technical:
        # Texnik xodim faqat o'ziga tayinlangan buyurtmalarni ko'radi
        return (order.assigned_measurer == user or 
                order.assigned_manufacturer == user or 
                order.assigned_installer == user)
    
    return False


def user_can_edit_order(user, order):
    """
    Foydalanuvchi buyurtmani tahrirlaya oladimi?
    """
    if user.is_admin or user.is_manager:
        return True
    
    if user.is_technical:
        # Texnik xodim faqat o'z bosqichida tahrirlaydi
        if order.status == 'measuring' and order.assigned_measurer == user:
            return user.can_measure
        elif order.status == 'processing' and order.assigned_manufacturer == user:
            return user.can_manufacture
        elif order.status == 'installing' and order.assigned_installer == user:
            return user.can_install
    
    return False


def user_can_manage_staff(user):
    """
    Foydalanuvchi xodimlarni boshqara oladimi?
    """
    return user.is_admin or user.is_manager


def user_can_view_reports(user):
    """
    Foydalanuvchi hisobotlarni ko'ra oladimi?
    """
    return user.is_admin or user.is_manager