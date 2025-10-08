"""Task chat message models.

This module defines the TaskChatMessage model for storing chat messages
associated with tasks, including user attribution and timestamps.
"""

from django.conf import settings
from django.db import models

from tasks.models import Task


class TaskChatMessage(models.Model):
    """Chat message associated with a task.

    Stores individual chat messages for task discussions with user
    attribution and automatic timestamp tracking.

    Attributes:
        task: Foreign key reference to the associated Task.
        user: Foreign key reference to the user who created the message.
        message: Text content of the chat message.
        timestamp: DateTime when the message was created (auto-populated).
    """

    task = models.ForeignKey(
        Task,
        related_name='chat_messages',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata configuration."""

        ordering = ['timestamp']

    def __str__(self):
        """Return string representation of the message.

        Returns:
            String containing username and first 50 characters of message.
        """
        return f"{self.user.username}: {self.message[:50]}"
