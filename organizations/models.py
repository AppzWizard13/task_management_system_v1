from django.conf import settings
from django.db import models
from django.contrib.auth.models import Permission


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("can_manage_organization", "Can manage organization"),
        ]

    def __str__(self):
        return self.name


class Department(models.Model):
    organization = models.ForeignKey(Organization, related_name='departments', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('organization', 'name')
        permissions = [
            ("can_manage_department", "Can manage department"),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.name}"


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='roles',
        help_text='Permissions assigned to this role',
    )

    def __str__(self):
        return self.name


class UserOrganizationRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_org_roles')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='user_org_roles')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='user_org_roles', null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_org_roles')

    class Meta:
        unique_together = ('user', 'organization', 'department', 'role')

    def __str__(self):
        dept_name = self.department.name if self.department else 'No Department'
        return f"{self.user} - {self.organization.name} - {dept_name} - {self.role.name}"
