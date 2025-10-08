"""Task management views.

This module contains all CRUD views for tasks, task output fields,
and task outputs with role-based permission controls and organization-level
data filtering for security.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.mixins import (
    OrganizationFilterMixin,
    OrganizationFormMixin,
    RolePermissionMixin,
)
from organizations.models import Department
from task_chat.models import TaskChatMessage

from .forms import (
    DynamicTaskCompletionForm,
    TaskForm,
    TaskOutputFieldForm,
    TaskOutputForm,
)
from .models import Task, TaskOutput, TaskOutputField


User = get_user_model()


@require_http_methods(["GET"])
def get_organization_data(request, org_id):
    """Return departments and users for a given organization.

    Used for AJAX requests to dynamically populate form fields.

    Args:
        request: HTTP request object.
        org_id: Organization ID integer.

    Returns:
        JsonResponse containing departments and users data with structure:
            {
                'departments': [{'id': 1, 'name': 'IT'}],
                'users': [{'id': 1, 'username': 'john', 'first_name': 'John'}]
            }
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        departments = list(
            Department.objects.filter(
                organization_id=org_id
            ).values('id', 'name')
        )
        users = list(
            User.objects.filter(
                user_org_roles__organization_id=org_id
            ).distinct().values('id', 'username', 'first_name', 'last_name')
        )

        return JsonResponse({
            'departments': departments,
            'users': users
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


class GenericFormMixin:
    """Provide common context data for form views.

    Attributes:
        model_name: Display name of the model.
        action: Action being performed (Add, Edit, Delete).
    """

    model_name = None
    action = None

    def get_context_data(self, **kwargs):
        """Add page title and submit button text to context.

        Returns:
            Dictionary containing context with page_title, submit_button,
            and success_url keys.
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"{self.action} {self.model_name}"
        context['submit_button'] = (
            "Save" if self.action in ['Add', 'Edit'] else "Confirm"
        )
        context['success_url'] = self.success_url or reverse_lazy(
            f"{self.model._meta.app_label}:{self.model._meta.model_name}_list"
        )
        return context


class TaskListView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    ListView
):
    """Display list of tasks filtered by user's organizations and access.

    Only shows tasks where user is assigned user, viewer, or superuser.
    Requires tasks.view_task permission.
    """

    model = Task
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10
    required_permission = 'tasks.view_task'

    def get_queryset(self):
        """Filter tasks based on user access.

        Returns:
            QuerySet of tasks where user is assigned or viewer.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()
        queryset = queryset.filter(organization__in=user_orgs)

        queryset = queryset.filter(
            Q(assigned_users=user) | Q(viewers=user)
        ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        """Add table configuration and permissions to context.

        Returns:
            Dictionary with page_title, item_name, URLs, table configuration,
            and permission keys.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Tasks',
            'item_name': 'Task',
            'add_url': 'tasks:task_add',
            'detail_url': 'tasks:task_detail',
            'edit_url': 'tasks:task_edit',
            'delete_url': 'tasks:task_delete',
            'table_headers': [
                'Name', 'Organization', 'Due Date', 'Created At'
            ],
            'list_attrs': ['name', 'organization', 'due_date', 'created_at'],
            'can_add': 'tasks.add_task',
            'can_edit': 'tasks.change_task',
            'can_delete': 'tasks.delete_task',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to dashboard on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'accounts:dashboard'


class TaskDetailView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    DetailView
):
    """Display task details with access control.

    Requires tasks.view_task permission.
    """

    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    required_permission = 'tasks.view_task'

    def get_context_data(self, **kwargs):
        """Add task details, outputs, and chat messages to context.

        Returns:
            Dictionary with task details, user outputs, completion status,
            chat messages, and navigation URLs.
        """
        context = super().get_context_data(**kwargs)
        task = self.get_object()

        user_outputs = TaskOutput.objects.filter(
            output_field__task=task,
            user=self.request.user
        ).select_related('output_field')

        has_completed = user_outputs.exists()

        chat_messages = TaskChatMessage.objects.filter(
            task=task
        ).select_related('user').order_by('timestamp')

        context.update({
            'page_title': 'Task Details',
            'edit_url': 'tasks:task_edit',
            'list_url': 'tasks:task_list',
            'fields': [field for field in self.model._meta.fields],
            'departments': task.departments.all(),
            'assigned_users': task.assigned_users.all(),
            'viewers': task.viewers.all(),
            'output_fields': task.output_fields.all(),
            'has_completed': has_completed,
            'user_outputs': user_outputs,
            'chat_messages': chat_messages,
            'can_edit': 'tasks.change_task',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to task list on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'tasks:task_list'


class TaskCreateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFormMixin,
    GenericFormMixin,
    CreateView,
):
    """Create new task with permission check and filtered choices.

    Requires tasks.add_task permission.
    """

    model = Task
    form_class = TaskForm
    template_name = 'tasks/advanced_task_create_form.html'
    success_url = reverse_lazy('tasks:task_list')
    model_name = "Task"
    action = "Add"
    required_permission = 'tasks.add_task'


class TaskUpdateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    OrganizationFormMixin,
    GenericFormMixin,
    UpdateView,
):
    """Update task with permission and access checks.

    Requires tasks.change_task permission.
    """

    model = Task
    form_class = TaskForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_list')
    model_name = "Task"
    action = "Edit"
    required_permission = 'tasks.change_task'


class TaskDeleteView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    GenericFormMixin,
    DeleteView,
):
    """Delete task with permission and access checks.

    Requires tasks.delete_task permission.
    """

    model = Task
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    model_name = "Task"
    action = "Delete"
    required_permission = 'tasks.delete_task'


class TaskOutputFieldListView(
    LoginRequiredMixin, OrganizationFilterMixin, ListView
):
    """Display list of task output fields filtered by user's organizations."""

    model = TaskOutputField
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        """Filter output fields by tasks in user's organizations.

        Returns:
            QuerySet of TaskOutputField objects.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()
        return queryset.filter(task__organization__id__in=user_orgs)

    def get_context_data(self, **kwargs):
        """Add table configuration and permissions to context.

        Returns:
            Dictionary with table headers, URLs, and permission keys.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Task Output Fields',
            'item_name': 'Task Output Field',
            'add_url': 'tasks:task_output_field_add',
            'detail_url': 'tasks:task_output_field_detail',
            'edit_url': 'tasks:task_output_field_edit',
            'delete_url': 'tasks:task_output_field_delete',
            'table_headers': ['Task', 'Name', 'Field Type', 'Required'],
            'list_attrs': ['task', 'name', 'field_type', 'required'],
            'can_add': 'task_outputs.add_taskoutputfield',
            'can_edit': 'task_outputs.change_taskoutputfield',
            'can_delete': 'task_outputs.delete_taskoutputfield',
        })
        return context


class TaskOutputFieldDetailView(
    LoginRequiredMixin, OrganizationFilterMixin, DetailView
):
    """Display task output field details."""

    model = TaskOutputField
    template_name = 'tasks/generic_detail.html'
    context_object_name = 'object'

    def get_queryset(self):
        """Filter output fields by tasks in user's organizations.

        Returns:
            QuerySet of TaskOutputField objects.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()
        return queryset.filter(task__organization__id__in=user_orgs)

    def get_context_data(self, **kwargs):
        """Add field list, permissions, and navigation URLs to context.

        Returns:
            Dictionary with fields, navigation URLs, and permissions.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Task Output Field',
            'edit_url': 'tasks:task_output_field_edit',
            'list_url': 'tasks:task_output_field_list',
            'fields': [field for field in self.model._meta.fields],
            'can_edit': 'task_outputs.change_taskoutputfield',
        })
        return context


class TaskOutputFieldCreateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    GenericFormMixin,
    CreateView,
):
    """Create task output field with permission check.

    Requires tasks.add_taskoutputfield permission.
    """

    model = TaskOutputField
    form_class = TaskOutputFieldForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_output_field_list')
    model_name = "Task Output Field"
    action = "Add"
    required_permission = 'tasks.add_taskoutputfield'

    def get_permission_denied_url(self):
        """Redirect to output field list on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'tasks:task_output_field_list'


class TaskOutputFieldUpdateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    GenericFormMixin,
    UpdateView,
):
    """Update task output field with permission check.

    Requires tasks.change_taskoutputfield permission.
    """

    model = TaskOutputField
    form_class = TaskOutputFieldForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_output_field_list')
    model_name = "Task Output Field"
    action = "Edit"
    required_permission = 'tasks.change_taskoutputfield'

    def get_queryset(self):
        """Filter output fields by tasks in user's organizations.

        Returns:
            QuerySet of TaskOutputField objects.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()
        return queryset.filter(task__organization__id__in=user_orgs)

    def get_permission_denied_url(self):
        """Redirect to output field list on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'tasks:task_output_field_list'


class TaskOutputFieldDeleteView(
    LoginRequiredMixin,
    RolePermissionMixin,
    GenericFormMixin,
    DeleteView,
):
    """Delete task output field with permission check.

    Requires tasks.delete_taskoutputfield permission.
    """

    model = TaskOutputField
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_output_field_list')
    model_name = "Task Output Field"
    action = "Delete"
    required_permission = 'tasks.delete_taskoutputfield'

    def get_queryset(self):
        """Filter output fields by tasks in user's organizations.

        Returns:
            QuerySet of TaskOutputField objects.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()
        return queryset.filter(task__organization__id__in=user_orgs)

    def get_permission_denied_url(self):
        """Redirect to output field list on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'tasks:task_output_field_list'


class TaskOutputListView(LoginRequiredMixin, ListView):
    """Display list of current user's task outputs."""

    model = TaskOutput
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        """Show only current user's outputs.

        Returns:
            QuerySet of TaskOutput objects for current user.
        """
        return TaskOutput.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add table configuration to context.

        Returns:
            Dictionary with table headers and navigation URLs.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'My Task Outputs',
            'item_name': 'Task Output',
            'add_url': 'tasks:task_output_add',
            'detail_url': 'tasks:task_output_detail',
            'edit_url': 'tasks:task_output_edit',
            'delete_url': 'tasks:task_output_delete',
            'table_headers': ['Output Field', 'Value', 'Submitted At'],
            'list_attrs': ['output_field', 'value_text', 'submitted_at'],
        })
        return context


class TaskOutputDetailView(LoginRequiredMixin, DetailView):
    """Display task output details for current user."""

    model = TaskOutput
    template_name = 'tasks/generic_detail.html'
    context_object_name = 'object'

    def get_queryset(self):
        """Filter to current user's outputs only.

        Returns:
            QuerySet of TaskOutput objects for current user.
        """
        return TaskOutput.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add field list and navigation URLs to context.

        Returns:
            Dictionary with fields and navigation URLs.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Task Output',
            'edit_url': 'tasks:task_output_edit',
            'list_url': 'tasks:task_output_list',
            'fields': [field for field in self.model._meta.fields],
        })
        return context


class TaskOutputCreateView(LoginRequiredMixin, GenericFormMixin, CreateView):
    """Create task output assigned to current user."""

    model = TaskOutput
    form_class = TaskOutputForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_output_list')
    model_name = "Task Output"
    action = "Submit"

    def form_valid(self, form):
        """Set user to current user before saving.

        Args:
            form: Validated TaskOutputForm instance.

        Returns:
            HttpResponse redirect to success_url.
        """
        form.instance.user = self.request.user
        return super().form_valid(form)


class TaskOutputUpdateView(LoginRequiredMixin, GenericFormMixin, UpdateView):
    """Update task output for current user's own outputs."""

    model = TaskOutput
    form_class = TaskOutputForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_output_list')
    model_name = "Task Output"
    action = "Edit"

    def get_queryset(self):
        """Users can only edit their own outputs.

        Returns:
            QuerySet of TaskOutput objects for current user.
        """
        return TaskOutput.objects.filter(user=self.request.user)


class TaskOutputDeleteView(LoginRequiredMixin, GenericFormMixin, DeleteView):
    """Delete task output for current user's own outputs."""

    model = TaskOutput
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_output_list')
    model_name = "Task Output"
    action = "Delete"

    def get_queryset(self):
        """Users can only delete their own outputs.

        Returns:
            QuerySet of TaskOutput objects for current user.
        """
        return TaskOutput.objects.filter(user=self.request.user)


class MyAssignedTasksListView(LoginRequiredMixin, ListView):
    """Display list of tasks assigned to current user."""

    model = Task
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        """Show only tasks assigned to current user.

        Returns:
            QuerySet of Task objects assigned to user.
        """
        return Task.objects.filter(
            assigned_users=self.request.user
        ).distinct()

    def get_context_data(self, **kwargs):
        """Add table configuration to context.

        Returns:
            Dictionary with table headers and navigation URLs.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'My Assigned Tasks',
            'item_name': 'Task',
            'detail_url': 'tasks:task_detail',
            'table_headers': ['Name', 'Organization', 'Due Date'],
            'list_attrs': ['name', 'organization', 'due_date'],
        })
        return context


class MyViewerTasksListView(LoginRequiredMixin, ListView):
    """Display list of tasks where user is a viewer."""

    model = Task
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        """Show only tasks where user is a viewer.

        Returns:
            QuerySet of Task objects where user is viewer.
        """
        return Task.objects.filter(viewers=self.request.user).distinct()

    def get_context_data(self, **kwargs):
        """Add table configuration to context.

        Returns:
            Dictionary with table headers and navigation URLs.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Tasks I Can View',
            'item_name': 'Task',
            'detail_url': 'tasks:task_detail',
            'table_headers': ['Name', 'Organization', 'Due Date'],
            'list_attrs': ['name', 'organization', 'due_date'],
        })
        return context


class TaskCompletionView(LoginRequiredMixin, View):
    """Handle task completion form for assigned users.

    Includes secure file handling with metadata storage and
    organization-level access control.
    """

    template_name = 'tasks/task_completion.html'

    def get(self, request, pk):
        """Display task completion form.

        Args:
            request: HTTP request object.
            pk: Task primary key integer.

        Returns:
            Rendered template with form and existing outputs.
        """
        task = get_object_or_404(Task, pk=pk)

        if not task.assigned_users.filter(id=request.user.id).exists():
            messages.error(request, "You are not assigned to this task.")
            return redirect('tasks:task_list')

        user_orgs = request.user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()
        if (not request.user.is_superuser and
                task.organization.id not in user_orgs):
            messages.error(request, "Access denied.")
            return redirect('tasks:task_list')

        existing_outputs = TaskOutput.objects.filter(
            output_field__task=task,
            user=request.user
        ).select_related('output_field')

        initial_data = {}
        existing_outputs_dict = {}

        for output in existing_outputs:
            field_name = f'field_{output.output_field.id}'
            existing_outputs_dict[output.output_field.id] = output

            if output.output_field.field_type != 'file':
                initial_data[field_name] = output.value_text

        form = DynamicTaskCompletionForm(
            task=task,
            user=request.user,
            initial=initial_data
        )

        context = {
            'task': task,
            'form': form,
            'has_submitted': existing_outputs.exists(),
            'existing_outputs': existing_outputs,
            'existing_outputs_dict': existing_outputs_dict,
        }

        return render(request, self.template_name, context)

    def post(self, request, pk):
        """Process task completion form submission.

        Handles file uploads with automatic metadata extraction and storage.

        Args:
            request: HTTP request with form data and files.
            pk: Task primary key integer.

        Returns:
            HttpResponse redirect to task detail on success, or re-rendered
            form on validation error.
        """
        task = get_object_or_404(Task, pk=pk)

        if not task.assigned_users.filter(id=request.user.id).exists():
            messages.error(request, "You are not assigned to this task.")
            return redirect('tasks:task_list')

        user_orgs = request.user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()
        if (not request.user.is_superuser and
                task.organization.id not in user_orgs):
            messages.error(request, "Access denied.")
            return redirect('tasks:task_list')

        form = DynamicTaskCompletionForm(
            task=task,
            user=request.user,
            data=request.POST,
            files=request.FILES
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    for field_name, value in form.cleaned_data.items():
                        if not field_name.startswith('field_'):
                            continue

                        field_id = int(field_name.split('_')[1])

                        try:
                            output_field = TaskOutputField.objects.get(
                                id=field_id
                            )
                        except TaskOutputField.DoesNotExist:
                            continue

                        if output_field.field_type == 'file':
                            if value:
                                output, created = (
                                    TaskOutput.objects.get_or_create(
                                        output_field=output_field,
                                        user=request.user,
                                        defaults={}
                                    )
                                )

                                if output.value_file:
                                    output.value_file.delete(save=False)

                                output.value_file = value
                                output.original_filename = value.name
                                output.file_size = value.size
                                output.save()
                        else:
                            if isinstance(value, list):
                                value = ', '.join(value)

                            TaskOutput.objects.update_or_create(
                                output_field=output_field,
                                user=request.user,
                                defaults={'value_text': str(value)}
                            )

                messages.success(
                    request,
                    "Task output submitted successfully!"
                )
                return redirect('tasks:task_detail', pk=task.pk)

            except Exception as e:
                messages.error(
                    request,
                    f"Error saving outputs: {str(e)}"
                )

        existing_outputs = TaskOutput.objects.filter(
            output_field__task=task,
            user=request.user
        ).select_related('output_field')

        existing_outputs_dict = {
            output.output_field.id: output
            for output in existing_outputs
        }

        context = {
            'task': task,
            'form': form,
            'has_submitted': existing_outputs.exists(),
            'existing_outputs': existing_outputs,
            'existing_outputs_dict': existing_outputs_dict,
        }

        return render(request, self.template_name, context)
