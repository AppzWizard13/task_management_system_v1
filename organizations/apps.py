"""Organizations application configuration.

This module defines the Django application configuration for the organizations
app, including default field settings and app metadata.
"""

from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    """Configuration class for the organizations application.

    Sets up application-level configuration including the default
    primary key field type and application name.

    Attributes:
        default_auto_field: Default primary key field type for models.
        name: Full Python path to the application.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizations'
