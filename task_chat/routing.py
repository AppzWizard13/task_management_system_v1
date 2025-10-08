"""WebSocket routing configuration for task chat.

Defines WebSocket URL patterns for real-time chat functionality.
"""

from django.urls import path

from . import consumers


websocket_urlpatterns = [
    path('ws/chat/<int:task_id>/', consumers.ChatConsumer.as_asgi()),
]
