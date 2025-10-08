"""Forms for organization management.

This module provides forms for creating and editing roles and user
role assignments with enhanced permission selection and validation.
"""

from django import forms
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from .models import Role, UserOrganizationRole


class RoleForm(forms.ModelForm):
    """Form for creating and editing roles with organized permissions.

    Provides a user-friendly interface for role management with
    checkbox-based permission selection grouped by application and model.
    """

    class Meta:
        """Form metadata configuration."""

        model = Role
        fields = ['name', 'description', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter role name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter role description'
            }),
            'permissions': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
        }
        help_texts = {
            'permissions': 'Select all permissions this role should have',
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with organized permission choices.

        Organizes permissions by application, content type, and action
        for better usability when assigning multiple permissions.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)

        if 'permissions' in self.fields:
            permissions = Permission.objects.select_related(
                'content_type'
            ).order_by(
                'content_type__app_label',
                'content_type__model',
                'codename'
            )

            self.fields['permissions'].queryset = permissions
            self.fields['permissions'].label_from_instance = (
                self.label_from_permission
            )

    @staticmethod
    def label_from_permission(obj):
        """Create readable label for permission display.

        Formats permission as 'App | Model | Action' for clarity.

        Args:
            obj: Permission instance to format.

        Returns:
            String formatted as 'App | Model | Action'.
        """
        app = obj.content_type.app_label.title()
        model = obj.content_type.model.replace('_', ' ').title()
        action = obj.name
        return f"{app} | {model} | {action}"


class UserOrganizationRoleForm(forms.ModelForm):
    """Form for creating and editing user role assignments.

    Manages the assignment of users to organizations with specific
    roles and optional department associations.
    """

    class Meta:
        """Form metadata configuration."""

        model = UserOrganizationRole
        fields = ['user', 'organization', 'department', 'role']

    def __init__(self, *args, **kwargs):
        """Initialize form with department field as optional.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.fields['department'].required = False
