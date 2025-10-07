from django import template

register = template.Library()

@register.filter
def attr(obj, attr_name):
    return getattr(obj, attr_name, '')


# organizations/templatetags/filter_extras.py
from django import template

register = template.Library()

@register.filter
def attr(obj, field_name):
    """
    Get attribute value from an object dynamically
    Usage: {{ object|attr:field.name }}
    """
    try:
        return getattr(obj, field_name, '-')
    except AttributeError:
        return '-'
