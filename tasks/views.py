# tasks/views.py
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView, DetailView,
    CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django import forms

from task_chat.models import TaskChatMessage
from .models import Task, TaskOutputField, TaskOutput
from organizations.models import Organization, Department
from django.contrib.auth import get_user_model
from django_select2.forms import ModelSelect2MultipleWidget



User = get_user_model()


class GenericFormMixin:
    model_name = None
    action = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"{self.action} {self.model_name}"
        context['submit_button'] = "Save" if self.action in ['Add', 'Edit'] else "Confirm"
        context['success_url'] = self.success_url or reverse_lazy(
            f"{self.model._meta.app_label}:{self.model._meta.model_name}_list"
        )
        return context


# ============ Task CRUD Views ============
class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Tasks',
            'item_name': 'Task',
            'add_url': 'tasks:task_add',
            'detail_url': 'tasks:task_detail',
            'edit_url': 'tasks:task_edit',
            'delete_url': 'tasks:task_delete',
            'table_headers': ['Name', 'Organization', 'Due Date', 'Created At'],
            'list_attrs': ['name', 'organization', 'due_date', 'created_at'],
        })
        return context



class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        
        # Check if current user has completed the task
        user_outputs = TaskOutput.objects.filter(
            output_field__task=task,
            user=self.request.user
        ).select_related('output_field')
        
        has_completed = user_outputs.exists()
        
        # Get chat messages for this task, ordered by timestamp
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
            'chat_messages': chat_messages,  # Add this line
        })
        return context

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'description', 'organization', 'departments', 'assigned_users', 'viewers', 'due_date']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'departments': forms.CheckboxSelectMultiple(),
            'assigned_users': forms.CheckboxSelectMultiple(),
            'viewers': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['organization'].widget.attrs['required'] = True
        self.fields['organization'].widget.attrs['class'] = 'form-select'
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['description'].widget.attrs['class'] = 'form-control'
        
        if self.instance.pk:
            self.fields['departments'].queryset = self.instance.organization.departments.all()
            self.fields['assigned_users'].queryset = User.objects.filter(
                user_org_roles__organization=self.instance.organization
            ).distinct()
            self.fields['viewers'].queryset = User.objects.filter(
                user_org_roles__organization=self.instance.organization
            ).distinct()
        elif 'organization' in self.data:
            # IMPORTANT: When form is submitted, filter by submitted organization
            try:
                org_id = int(self.data.get('organization'))
                self.fields['departments'].queryset = Department.objects.filter(organization_id=org_id)
                self.fields['assigned_users'].queryset = User.objects.filter(
                    user_org_roles__organization_id=org_id
                ).distinct()
                self.fields['viewers'].queryset = User.objects.filter(
                    user_org_roles__organization_id=org_id
                ).distinct()
            except (ValueError, TypeError):
                pass
        else:
            # Show all initially (AJAX will filter)
            self.fields['departments'].queryset = Department.objects.all()
            self.fields['assigned_users'].queryset = User.objects.all()
            self.fields['viewers'].queryset = User.objects.all()



from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def get_organization_data(request, org_id):
    """Return departments and users for a given organization"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        departments = list(
            Department.objects.filter(organization_id=org_id).values('id', 'name')
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



class TaskCreateView(LoginRequiredMixin, GenericFormMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/advanced_task_create_form.html'
    success_url = reverse_lazy('tasks:task_list')
    model_name = "Task"
    action = "Add"


class TaskUpdateView(LoginRequiredMixin, GenericFormMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_list')
    model_name = "Task"
    action = "Edit"


class TaskDeleteView(LoginRequiredMixin, GenericFormMixin, DeleteView):
    model = Task
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    model_name = "Task"
    action = "Delete"


# ============ Task Output Field Views ============
class TaskOutputFieldForm(forms.ModelForm):
    class Meta:
        model = TaskOutputField
        fields = ['task', 'name', 'field_type', 'required', 'options', 'min_value', 'max_value']
        widgets = {
            'options': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Comma-separated options for radio/checkbox'}),
        }


class TaskOutputFieldListView(LoginRequiredMixin, ListView):
    model = TaskOutputField
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
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
        })
        return context


class TaskOutputFieldDetailView(LoginRequiredMixin, DetailView):
    model = TaskOutputField
    template_name = 'tasks/generic_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Task Output Field',
            'edit_url': 'tasks:task_output_field_edit',
            'list_url': 'tasks:task_output_field_list',
            'fields': [field for field in self.model._meta.fields],
        })
        return context


class TaskOutputFieldCreateView(LoginRequiredMixin, GenericFormMixin, CreateView):
    model = TaskOutputField
    form_class = TaskOutputFieldForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_output_field_list')
    model_name = "Task Output Field"
    action = "Add"


class TaskOutputFieldUpdateView(LoginRequiredMixin, GenericFormMixin, UpdateView):
    model = TaskOutputField
    form_class = TaskOutputFieldForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_output_field_list')
    model_name = "Task Output Field"
    action = "Edit"


class TaskOutputFieldDeleteView(LoginRequiredMixin, GenericFormMixin, DeleteView):
    model = TaskOutputField
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_output_field_list')
    model_name = "Task Output Field"
    action = "Delete"


# ============ Task Output Views (For User Submission) ============
class TaskOutputForm(forms.ModelForm):
    class Meta:
        model = TaskOutput
        fields = ['output_field', 'value_text', 'value_file']


class TaskOutputListView(LoginRequiredMixin, ListView):
    model = TaskOutput
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        # Show only current user's outputs
        return TaskOutput.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
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
    model = TaskOutput
    template_name = 'tasks/generic_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Task Output',
            'edit_url': 'tasks:task_output_edit',
            'list_url': 'tasks:task_output_list',
            'fields': [field for field in self.model._meta.fields],
        })
        return context


class TaskOutputCreateView(LoginRequiredMixin, GenericFormMixin, CreateView):
    model = TaskOutput
    form_class = TaskOutputForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_output_list')
    model_name = "Task Output"
    action = "Submit"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TaskOutputUpdateView(LoginRequiredMixin, GenericFormMixin, UpdateView):
    model = TaskOutput
    form_class = TaskOutputForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('tasks:task_output_list')
    model_name = "Task Output"
    action = "Edit"

    def get_queryset(self):
        # Users can only edit their own outputs
        return TaskOutput.objects.filter(user=self.request.user)


class TaskOutputDeleteView(LoginRequiredMixin, GenericFormMixin, DeleteView):
    model = TaskOutput
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_output_list')
    model_name = "Task Output"
    action = "Delete"

    def get_queryset(self):
        return TaskOutput.objects.filter(user=self.request.user)


# ============ My Assigned Tasks View ============
class MyAssignedTasksListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        # Show only tasks assigned to current user using ManyToMany
        return Task.objects.filter(assigned_users=self.request.user).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'My Assigned Tasks',
            'item_name': 'Task',
            'detail_url': 'tasks:task_detail',
            'table_headers': ['Name', 'Organization', 'Due Date'],
            'list_attrs': ['name', 'organization', 'due_date'],
        })
        return context


# ============ My Viewer Tasks View ============
class MyViewerTasksListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        # Show only tasks where user is a viewer using ManyToMany
        return Task.objects.filter(viewers=self.request.user).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Tasks I Can View',
            'item_name': 'Task',
            'detail_url': 'tasks:task_detail',
            'table_headers': ['Name', 'Organization', 'Due Date'],
            'list_attrs': ['name', 'organization', 'due_date'],
        })
        return context


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Task, TaskOutput
from .forms import DynamicTaskCompletionForm


class TaskCompletionView(LoginRequiredMixin, View):
    template_name = 'tasks/task_completion.html'
    
    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        
        # Check if user is assigned to this task
        if not task.assigned_users.filter(id=request.user.id).exists():
            messages.error(request, "You are not assigned to this task.")
            return redirect('tasks:task_list')
        
        # Check if user has already submitted
        existing_outputs = TaskOutput.objects.filter(
            output_field__task=task,
            user=request.user
        ).select_related('output_field')
        
        # Prepare initial data for form
        initial_data = {}
        for output in existing_outputs:
            field_name = f'field_{output.output_field.id}'
            if output.output_field.field_type == 'file':
                # For file fields, we'll show the existing file link in template
                pass
            else:
                initial_data[field_name] = output.value_text
        
        form = DynamicTaskCompletionForm(task=task, user=request.user, initial=initial_data)
        
        context = {
            'task': task,
            'form': form,
            'has_submitted': existing_outputs.exists(),
            'existing_outputs': existing_outputs,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        
        # Check if user is assigned
        if not task.assigned_users.filter(id=request.user.id).exists():
            messages.error(request, "You are not assigned to this task.")
            return redirect('tasks:task_list')
        
        form = DynamicTaskCompletionForm(task=task, user=request.user, data=request.POST, files=request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Task output submitted successfully!")
            return redirect('tasks:task_detail', pk=task.pk)
        
        # Get existing outputs for re-rendering on error
        existing_outputs = TaskOutput.objects.filter(
            output_field__task=task,
            user=request.user
        ).select_related('output_field')
        
        context = {
            'task': task,
            'form': form,
            'has_submitted': existing_outputs.exists(),
            'existing_outputs': existing_outputs,
        }
        
        return render(request, self.template_name, context)
