"""Task chat URL configuration.

This module defines URL patterns for task chat functionality,
mapping WebSocket and HTTP endpoints to their respective views.
"""

from django.urls import path

from . import views


app_name = 'task_chat'


urlpatterns = [
    path('<int:task_id>/', views.task_chat_view, name='chat'),
]
