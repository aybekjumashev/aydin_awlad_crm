# accounts/templatetags/__init__.py
# Bu fayl bo'sh qolishi kerak

# accounts/templatetags/math_filters.py

from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide the value by the argument."""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sub(value, arg):
    """Subtract the argument from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_float(value, arg):
    """Add the argument to the value."""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0