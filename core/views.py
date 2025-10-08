# core/views.py

"""Secure file serving with access control."""

import mimetypes
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from tasks.models import TaskOutput


@login_required
def serve_protected_file(request, output_id):
    """
    Serve file with access control checks.

    Args:
        request: HTTP request
        output_id: TaskOutput ID

    Returns:
        FileResponse: Protected file if user has access
        Http404: If file not found or access denied
    """
    output = get_object_or_404(TaskOutput, id=output_id)
    user = request.user

    if not has_file_access(user, output):
        raise Http404("File not found or access denied")

    if not output.value_file:
        raise Http404("File not found")

    try:
        file_handle = output.value_file.open('rb')
        
        content_type, _ = mimetypes.guess_type(output.original_filename)
        if not content_type:
            content_type = 'application/octet-stream'
        
        response = FileResponse(file_handle, content_type=content_type)
        response['Content-Disposition'] = (
            f'attachment; filename="{output.original_filename}"'
        )
        response['X-Content-Type-Options'] = 'nosniff'
        response['Content-Security-Policy'] = "default-src 'none'"
        
        return response
        
    except Exception as e:
        raise Http404(f"Error serving file: {str(e)}")


def has_file_access(user, task_output):
    """
    Check if user has access to the task output file.

    Args:
        user: User instance
        task_output: TaskOutput instance

    Returns:
        bool: True if user has access, False otherwise
    """
    if user.is_superuser:
        return True

    task = task_output.output_field.task

    if task_output.user == user:
        return True

    user_orgs = user.user_org_roles.values_list(
        'organization', flat=True
    ).distinct()

    if task.organization.id not in user_orgs:
        return False

    if user in task.assigned_users.all() or user in task.viewers.all():
        return True

    return False
