# task_chat/routing.py

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:task_id>/', consumers.ChatConsumer.as_asgi()),
]
