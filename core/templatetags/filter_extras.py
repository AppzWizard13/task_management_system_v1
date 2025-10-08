"""Template filters for dynamic attribute access.

Provides custom template filter for accessing object attributes dynamically.
"""

from django import template


register = template.Library()


@register.filter
def attr(obj, field_name):
    """Get attribute value from an object dynamically.

    Args:
        obj: Object to retrieve attribute from.
        field_name: Name of the attribute to access.

    Returns:
        Attribute value or '-' if not found.

    Example:
        In template: {{ object|attr:field.name }}
    """
    try:
        return getattr(obj, field_name, '-')
    except AttributeError:
        return '-'
