from django.conf import settings
from django.db import models
from organizations.models import Organization, Department


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
        upload_to='task_outputs/', 
        blank=True, 
        null=True
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
