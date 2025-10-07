# task_chat/views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from tasks.models import Task
from .models import TaskChatMessage

@login_required
def task_chat_view(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    messages = TaskChatMessage.objects.filter(task=task).select_related('user')
    
    context = {
        'task': task,
        'messages': messages,
    }
    return render(request, 'chat.html', context)
