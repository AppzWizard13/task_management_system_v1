"""Organization management models.

This module defines models for organizations, departments, roles,
and user role assignments with permission management.
"""

from django.conf import settings
from django.contrib.auth.models import Permission
from django.db import models


class Organization(models.Model):
    """Organization entity for multi-tenant management.

    Represents a top-level organizational unit that can contain
    departments, users, and has associated permissions.

    Attributes:
        name: Unique organization name.
        description: Optional text description of the organization.
        created_at: DateTime when organization was created (auto-populated).
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata configuration."""

        permissions = [
            ("can_manage_organization", "Can manage organization"),
        ]

    def __str__(self):
        """Return string representation of the organization.

        Returns:
            Organization name.
        """
        return self.name


class Department(models.Model):
    """Department within an organization.

    Represents a subdivision of an organization with its own
    identity and user assignments.

    Attributes:
        organization: Foreign key reference to parent Organization.
        name: Department name (unique within organization).
        description: Optional text description of the department.
    """

    organization = models.ForeignKey(
        Organization,
        related_name='departments',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        """Model metadata configuration."""

        unique_together = ('organization', 'name')
        permissions = [
            ("can_manage_department", "Can manage department"),
        ]

    def __str__(self):
        """Return string representation of the department.

        Returns:
            String format: 'Organization - Department'.
        """
        return f"{self.organization.name} - {self.name}"


class Role(models.Model):
    """Role for permission management.

    Defines a named set of permissions that can be assigned
    to users within organizations.

    Attributes:
        name: Unique role name.
        description: Optional text description of the role.
        permissions: Many-to-many relationship to Django permissions.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='roles',
        help_text='Permissions assigned to this role',
    )

    def __str__(self):
        """Return string representation of the role.

        Returns:
            Role name.
        """
        return self.name


class UserOrganizationRole(models.Model):
    """User role assignment within an organization.

    Links users to organizations with specific roles and optional
    department assignment for granular access control.

    Attributes:
        user: Foreign key reference to User model.
        organization: Foreign key reference to Organization.
        department: Optional foreign key reference to Department.
        role: Foreign key reference to Role.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_org_roles'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='user_org_roles'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='user_org_roles',
        null=True,
        blank=True
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_org_roles'
    )

    class Meta:
        """Model metadata configuration."""

        unique_together = ('user', 'organization', 'department', 'role')

    def __str__(self):
        """Return string representation of the user role assignment.

        Returns:
            String format: 'User - Organization - Department - Role'.
        """
        dept_name = self.department.name if self.department else 'No Department'
        return (
            f"{self.user} - {self.organization.name} - "
            f"{dept_name} - {self.role.name}"
        )
