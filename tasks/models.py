# tasks/models.py

"""
Task models for managing tasks, output fields, and user submissions.

This module defines tasks within organizations with secure file upload handling.
"""

import os
import uuid
from django.conf import settings
from django.db import models
from organizations.models import Organization, Department


def task_output_upload_path(instance, filename):
    """
    Generate secure upload path with UUID and sanitized filename.

    Path structure: task_outputs/org_<id>/task_<id>/user_<id>/<uuid>_<filename>

    Args:
        instance: TaskOutput instance
        filename: Original filename

    Returns:
        str: Secure upload path
    """
    from core.validators import sanitize_filename
    
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Get file extension
    ext = os.path.splitext(safe_filename)[1]
    
    # Generate UUID-based filename
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # Build path components
    org_id = instance.output_field.task.organization.id
    task_id = instance.output_field.task.id
    user_id = instance.user.id
    
    return f'task_outputs/org_{org_id}/task_{task_id}/user_{user_id}/{unique_filename}'


class Task(models.Model):
    """
    Main Task model representing a task within an organization.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization, 
        related_name='tasks', 
        on_delete=models.CASCADE,
        help_text='Organization this task belongs to'
    )
    departments = models.ManyToManyField(
        Department, 
        related_name='tasks',
        blank=True,
        help_text='Departments this task is associated with'
    )
    
    # Users who can edit and complete the task
    assigned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_tasks',
        blank=True,
        help_text='Users assigned to complete this task'
    )
    
    # Users who can only view the task
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='viewed_tasks',
        blank=True,
        help_text='Users who can only view this task'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class TaskOutputField(models.Model):
    """
    Defines output fields for a task (forms/inputs users need to fill).
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('radio', 'Radio'),
        ('checkbox', 'Checkbox'),
        ('yesno', 'Yes/No'),
        ('number', 'Number'),
        ('file', 'File Upload'),
    ]
    
    task = models.ForeignKey(
        Task, 
        related_name='output_fields', 
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    required = models.BooleanField(default=True)
    
    # For radio/checkbox: options stored as comma separated values or JSON
    options = models.TextField(
        blank=True, 
        null=True, 
        help_text="Comma separated options for radio/checkbox fields"
    )
    
    # For number field validation
    min_value = models.FloatField(
        null=True, 
        blank=True,
        help_text="Minimum value for number fields"
    )
    max_value = models.FloatField(
        null=True, 
        blank=True,
        help_text="Maximum value for number fields"
    )
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Task Output Field'
        verbose_name_plural = 'Task Output Fields'
    
    def __str__(self):
        return f"{self.task.name} - {self.name} ({self.field_type})"


class TaskOutput(models.Model):
    """
    Stores the actual output/response submitted by users for task fields.
    
    Includes secure file upload handling with metadata storage.
    """
    output_field = models.ForeignKey(
        TaskOutputField, 
        related_name='outputs', 
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='task_outputs', 
        on_delete=models.CASCADE
    )
    value_text = models.TextField(blank=True, null=True)
    value_file = models.FileField(
        upload_to=task_output_upload_path,  # Changed to use secure function
        blank=True, 
        null=True,
        max_length=500  # Added for longer paths
    )
    # New fields for secure file handling
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        help_text='Original filename before sanitization'
    )
    file_size = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='File size in bytes'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Task Output'
        verbose_name_plural = 'Task Outputs'
        # Prevent duplicate submissions for the same field by the same user
        unique_together = ('output_field', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.output_field.name} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Save original filename and file size for uploaded files."""
        if self.value_file:
            self.original_filename = os.path.basename(self.value_file.name)
            self.file_size = self.value_file.size
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Delete file from storage when output is deleted."""
        if self.value_file:
            self.value_file.delete(save=False)
        super().delete(*args, **kwargs)
    
    def get_file_size_display(self):
        """
        Get human-readable file size.
        
        Returns:
            str: Formatted file size (e.g., "2.5 MB")
        """
        if not self.file_size:
            return "Unknown"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
