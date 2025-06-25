# templatetags/custom_filters.py
# Template'lar uchun custom filter'lar

from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Ayirish amali uchun filter"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Ko'paytirish amali uchun filter"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """Foiz hisoblash uchun filter"""
    try:
        return (float(value) / float(arg)) * 100 if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0


@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)