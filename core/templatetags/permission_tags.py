"""Template tags for permission checking.

This module provides custom template filters for checking user permissions
through role-based access control in templates.
"""

from django import template


register = template.Library()


@register.filter
def has_permission(user, permission_codename):
    """Check if user has a specific permission through their role.

    Validates user permissions against roles assigned through
    UserOrganizationRole relationships. Superusers automatically
    have all permissions.

    Args:
        user: User instance to check permissions for.
        permission_codename: Permission string in format 'app_label.codename'
                           (e.g., 'organizations.add_organization').

    Returns:
        Boolean indicating whether user has the specified permission.

    Example:
        In template: {% if request.user|has_permission:'organizations.add_organization' %}
    """
    if user.is_superuser:
        return True

    if not permission_codename or '.' not in permission_codename:
        return False

    app_label, codename = permission_codename.split('.')

    for user_role in user.user_org_roles.all():
        if user_role.role.permissions.filter(
            content_type__app_label=app_label,
            codename=codename
        ).exists():
            return True

    return False
