"""Mixins for organization-based access control and filtering.

This module provides reusable mixins for role-based permission checking,
organization-level data filtering, and form field filtering based on
user's organization access.
"""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class RolePermissionMixin(UserPassesTestMixin):
    """Check if user has permission through their assigned role.

    Validates user permissions against roles assigned through
    UserOrganizationRole relationships. Requires setting
    required_permission attribute on the view.

    Attributes:
        required_permission: Permission string (e.g., 'app.codename').
        permission_denied_message: Message displayed on permission denial.
    """

    required_permission = None
    permission_denied_message = (
        "You don't have permission to perform this action."
    )

    def test_func(self):
        """Test if user has required permission.

        Checks superuser status first, then validates permission
        through user's assigned roles in organizations.

        Returns:
            Boolean indicating whether user has permission.
        """
        if not self.required_permission:
            return True

        user = self.request.user

        if user.is_superuser:
            return True

        app_label, codename = self.required_permission.split('.')

        for user_role in user.user_org_roles.all():
            if user_role.role.permissions.filter(
                content_type__app_label=app_label,
                codename=codename
            ).exists():
                return True

        return False

    def handle_no_permission(self):
        """Handle permission denial with error message and redirect.

        Returns:
            HttpResponse redirect to permission denied URL.
        """
        messages.error(self.request, self.permission_denied_message)
        redirect_url = self.get_permission_denied_url()
        return redirect(redirect_url)

    def get_permission_denied_url(self):
        """Get URL to redirect to on permission denial.

        Override this method to customize redirect behavior.

        Returns:
            String URL name for redirect (defaults to model list view).
        """
        model_name = self.model._meta.model_name
        return f'{self.model._meta.app_label}:{model_name}_list'


class OrganizationFilterMixin:
    """Filter queryset based on user's organizations.

    Ensures users only see data from organizations they belong to,
    with automatic filtering based on model relationships.
    """

    def get_queryset(self):
        """Filter queryset to user's accessible organizations.

        Applies organization-level filtering based on model type
        and user's organization memberships.

        Returns:
            Filtered QuerySet containing only accessible records.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()

        model_name = self.model.__name__.lower()

        if model_name == 'organization':
            return queryset.filter(id__in=user_orgs)
        elif model_name == 'department':
            return queryset.filter(organization__id__in=user_orgs)
        elif model_name == 'userorganizationrole':
            return queryset.filter(organization__id__in=user_orgs)
        elif model_name == 'task':
            return queryset.filter(organization__id__in=user_orgs)
        elif model_name == 'taskassignment':
            return queryset.filter(task__organization__id__in=user_orgs)
        elif model_name == 'taskviewer':
            return queryset.filter(task__organization__id__in=user_orgs)

        return queryset


class OrganizationFormMixin:
    """Filter form choices based on user's organizations.

    Limits dropdown options in forms to only show organizations
    and departments accessible to the current user.
    """

    def get_form(self, form_class=None):
        """Get form with filtered organization and department choices.

        Applies querysets to organization and department fields
        that only include records accessible to the user.

        Args:
            form_class: Optional form class to instantiate.

        Returns:
            Form instance with filtered field choices.
        """
        form = super().get_form(form_class)
        user = self.request.user

        if user.is_superuser:
            return form

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()

        if 'organization' in form.fields:
            from organizations.models import Organization
            form.fields['organization'].queryset = (
                Organization.objects.filter(id__in=user_orgs)
            )

        if 'department' in form.fields:
            from organizations.models import Department
            form.fields['department'].queryset = (
                Department.objects.filter(organization__id__in=user_orgs)
            )

        return form
