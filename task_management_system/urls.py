"""URL configuration for task_management_system project.

This module defines the main URL routing for the task management system,
including admin, authentication, organizations, tasks, and protected file
serving endpoints.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts.views import DashboardView
from core.views import serve_protected_file


urlpatterns = [
    path('admin/', admin.site.urls),
    path('select2/', include('django_select2.urls')),
    path('', include('accounts.urls')),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('organizations/', include('organizations.urls')),
    path('tasks/', include('tasks.urls')),
    path('task-chat/', include('task_chat.urls')),
    path(
        'protected/file/<int:output_id>/',
        serve_protected_file,
        name='serve_protected_file'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
