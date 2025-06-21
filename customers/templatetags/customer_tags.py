# customers/templatetags/customer_tags.py

from django import template

register = template.Library()

@register.filter
def category_badge_class(category):
    """Mijoz kategoriyasi uchun Bootstrap badge klassi"""
    classes = {
        'new': 'primary',
        'regular': 'success', 
        'vip': 'warning',
        'inactive': 'secondary'
    }
    return classes.get(category, 'secondary')

@register.filter
def format_phone(phone):
    """Telefon raqamni formatlash"""
    if not phone:
        return ''
    
    # +998901234567 -> +998 (90) 123-45-67
    if len(phone) == 13 and phone.startswith('+998'):
        return f"+998 ({phone[4:6]}) {phone[6:9]}-{phone[9:11]}-{phone[11:13]}"
    
    return phone

@register.filter
def order_status_badge(status):
    """Buyurtma holati uchun badge klassi"""
    classes = {
        'new': 'primary',
        'measuring': 'info',
        'in_progress': 'warning', 
        'installed': 'success',
        'cancelled': 'danger'
    }
    return classes.get(status, 'secondary')