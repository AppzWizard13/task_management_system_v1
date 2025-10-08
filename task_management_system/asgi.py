"""ASGI configuration for task_management_system project.

This module configures ASGI for both HTTP and WebSocket protocols,
including authentication middleware and origin validation for WebSocket
connections.

For more information on ASGI deployment, see:
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'task_management_system.settings'
)

django_asgi_app = get_asgi_application()

from task_chat.routing import websocket_urlpatterns


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
