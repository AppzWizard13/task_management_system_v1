"""Custom user model for extended authentication.

This module defines the CustomUser model extending Django's AbstractUser
with additional fields and customized group/permission relationships.
"""

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class CustomUser(AbstractUser):
    """Extended user model with additional profile information.

    Extends Django's AbstractUser with phone number field and
    customized related names for groups and permissions to avoid
    conflicts with default User model.

    Attributes:
        phone_number: Optional phone number for user contact.
        groups: Many-to-many relationship to Group model.
        user_permissions: Many-to-many relationship to Permission model.
    """

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all '
            'permissions granted to each of their groups.'
        ),
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
