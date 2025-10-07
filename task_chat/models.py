# task_chat/models.py - Already correct!
from django.conf import settings
from django.db import models
from tasks.models import Task

class TaskChatMessage(models.Model):
    task = models.ForeignKey(Task, related_name='chat_messages', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"
