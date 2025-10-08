"""WebSocket consumer for task chat functionality.

This module provides asynchronous WebSocket consumer for real-time
task chat messaging using Django Channels.
"""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone

from tasks.models import Task

from .models import TaskChatMessage


User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time task chat.

    Handles WebSocket connections for task-specific chat rooms,
    manages message broadcasting to all connected clients, and
    persists messages to the database.

    Attributes:
        task_id: ID of the task associated with this chat room.
        room_group_name: Unique identifier for the chat room group.
    """

    async def connect(self):
        """Handle WebSocket connection.

        Extracts task ID from URL, creates room group name, adds
        the channel to the room group, and accepts the connection.
        """
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'chat_{self.task_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection.

        Removes the channel from the room group when connection closes.

        Args:
            close_code: WebSocket close code indicating reason for closure.
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Receive and process message from WebSocket.

        Parses incoming message, saves to database, and broadcasts
        to all clients in the room group.

        Args:
            text_data: JSON string containing message data.
        """
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user = self.scope['user']

        await self.save_message(user, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': user.username,
                'timestamp': str(await self.get_timestamp())
            }
        )

    async def chat_message(self, event):
        """Receive message from room group and send to WebSocket.

        Handles messages broadcast from the room group and sends
        them to the connected WebSocket client.

        Args:
            event: Dictionary containing message, username, and timestamp.
        """
        message = event['message']
        username = event['username']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def save_message(self, user, message):
        """Save chat message to database.

        Creates a new TaskChatMessage record in the database
        with the provided user and message content.

        Args:
            user: User instance who sent the message.
            message: Text content of the message.

        Returns:
            TaskChatMessage instance that was created.
        """
        task = Task.objects.get(id=self.task_id)
        chat_msg = TaskChatMessage.objects.create(
            task=task,
            user=user,
            message=message
        )
        return chat_msg

    @database_sync_to_async
    def get_timestamp(self):
        """Get current timestamp.

        Returns:
            DateTime object representing current time in configured timezone.
        """
        return timezone.now()
