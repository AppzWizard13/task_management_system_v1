"""Task chat view module.

This module provides view functions for displaying and managing
task-related chat messages with user authentication.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from tasks.models import Task

from .models import TaskChatMessage


@login_required
def task_chat_view(request, task_id):
    """Display chat messages for a specific task.

    Retrieves and displays all chat messages associated with a task,
    along with user information for each message. Requires user
    authentication to access.

    Args:
        request: HTTP request object containing user session data.
        task_id: Primary key integer of the task to display chat for.

    Returns:
        HttpResponse: Rendered chat template with task and messages context.

    Raises:
        Http404: If task with given task_id does not exist.
    """
    task = get_object_or_404(Task, pk=task_id)
    messages = TaskChatMessage.objects.filter(
        task=task
    ).select_related('user')

    context = {
        'task': task,
        'messages': messages,
    }
    return render(request, 'chat.html', context)
