"""User account and authentication views.

This module handles user authentication, registration, user management CRUD
operations, and the main dashboard with role-based filtering.
"""

from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import FormView

from core.mixins import OrganizationFilterMixin, RolePermissionMixin
from organizations.models import Department, Organization, UserOrganizationRole
from tasks.models import Task, TaskOutput

from .models import CustomUser


User = get_user_model()


class UserLoginView(LoginView):
    """Handle user login with custom template."""

    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class UserRegisterView(FormView):
    """Handle new user registration with automatic login."""

    template_name = 'accounts/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        """Save user and log them in automatically.

        Args:
            form: Validated UserCreationForm instance.

        Returns:
            HttpResponse redirect to success_url.
        """
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)


class UserLogoutView(LogoutView):
    """Handle user logout."""

    next_page = reverse_lazy('accounts:login')


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


class UserListView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    ListView
):
    """Display list of users filtered by user's organizations.

    Requires accounts.view_customuser permission.
    """

    model = CustomUser
    template_name = 'accounts/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10
    required_permission = 'accounts.view_customuser'

    def get_queryset(self):
        """Filter users based on current user's organization access.

        Returns:
            QuerySet of CustomUser objects accessible to current user.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()

        return queryset.filter(
            user_org_roles__organization__in=user_orgs
        ).distinct()

    def get_context_data(self, **kwargs):
        """Add table configuration and permissions to context.

        Returns:
            Dictionary with page_title, table headers, URLs,
            and permission keys.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Users',
            'item_name': 'User',
            'add_url': 'accounts:user_add',
            'detail_url': 'accounts:user_detail',
            'edit_url': 'accounts:user_edit',
            'delete_url': 'accounts:user_delete',
            'table_headers': [
                'Username', 'Email', 'Phone Number', 'Active'
            ],
            'list_attrs': [
                'username', 'email', 'phone_number', 'is_active'
            ],
            'can_add': 'accounts.add_customuser',
            'can_edit': 'accounts.change_customuser',
            'can_delete': 'accounts.delete_customuser',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to dashboard on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'accounts:dashboard'


class UserDetailView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    DetailView
):
    """Display user details.

    Requires accounts.view_customuser permission.
    """

    model = CustomUser
    template_name = 'accounts/user_detail.html'
    context_object_name = 'object'
    required_permission = 'accounts.view_customuser'

    def get_queryset(self):
        """Filter users based on current user's organization access.

        Returns:
            QuerySet of CustomUser objects accessible to current user.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()

        return queryset.filter(
            user_org_roles__organization__in=user_orgs
        ).distinct()

    def get_context_data(self, **kwargs):
        """Add navigation URLs and permissions to context.

        Returns:
            Dictionary with page_title, navigation URLs, and permissions.
        """
        context = super().get_context_data(**kwargs)

        context.update({
            'page_title': 'User Details',
            'edit_url': 'accounts:user_edit',
            'list_url': 'accounts:user_list',
            'can_edit': 'accounts.change_customuser',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to user list on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'accounts:user_list'


class UserCreateView(
    LoginRequiredMixin, RolePermissionMixin, GenericFormMixin, CreateView
):
    """Create new user with permission check.

    Requires accounts.add_customuser permission.
    """

    model = CustomUser
    fields = [
        'username', 'first_name', 'last_name', 'email',
        'phone_number', 'password'
    ]
    template_name = 'accounts/generic_form.html'
    success_url = reverse_lazy('accounts:user_list')
    model_name = "User"
    action = "Add"
    required_permission = 'accounts.add_customuser'

    def form_valid(self, form):
        """Hash password before saving user.

        Args:
            form: Validated form instance.

        Returns:
            HttpResponse redirect to success_url.
        """
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        return super().form_valid(form)


class UserUpdateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    GenericFormMixin,
    UpdateView,
):
    """Update user with permission and access checks.

    Requires accounts.change_customuser permission.
    """

    model = CustomUser
    fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
    template_name = 'accounts/generic_form.html'
    success_url = reverse_lazy('accounts:user_list')
    model_name = "User"
    action = "Edit"
    required_permission = 'accounts.change_customuser'

    def get_queryset(self):
        """Filter users based on current user's organization access.

        Returns:
            QuerySet of CustomUser objects accessible to current user.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()

        return queryset.filter(
            user_org_roles__organization__in=user_orgs
        ).distinct()


class UserDeleteView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    GenericFormMixin,
    DeleteView,
):
    """Delete user with permission and access checks.

    Requires accounts.delete_customuser permission.
    """

    model = CustomUser
    template_name = 'accounts/generic_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')
    model_name = "User"
    action = "Delete"
    required_permission = 'accounts.delete_customuser'

    def get_queryset(self):
        """Filter users based on current user's organization access.

        Returns:
            QuerySet of CustomUser objects accessible to current user.
        """
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        user_orgs = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()

        return queryset.filter(
            user_org_roles__organization__in=user_orgs
        ).distinct()


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view with statistics and task overview.

    Displays filtered data based on user's organization access with
    filtering options for organizations, departments, and users.
    Shows only tasks where user is assigned or viewer.
    """

    template_name = 'dashboard.html'
    login_url = '/login/'
    redirect_field_name = 'next'

    def get_user_organizations(self, user):
        """Get organizations accessible by the user.

        Args:
            user: Current user instance.

        Returns:
            QuerySet of Organization objects user has access to.
        """
        if user.is_superuser:
            return Organization.objects.all()

        user_org_ids = user.user_org_roles.values_list(
            'organization', flat=True
        ).distinct()
        return Organization.objects.filter(id__in=user_org_ids)

    def get_user_departments(self, user, organizations):
        """Get departments accessible by the user.

        Args:
            user: Current user instance.
            organizations: QuerySet of user's organizations.

        Returns:
            Tuple of (all_departments, user_specific_departments).
        """
        if user.is_superuser:
            all_depts = Department.objects.all()
            return all_depts, all_depts

        user_org_ids = organizations.values_list('id', flat=True)
        all_depts = Department.objects.filter(
            organization__id__in=user_org_ids
        )

        user_dept_ids = user.user_org_roles.filter(
            department__isnull=False
        ).values_list('department', flat=True).distinct()

        user_depts = Department.objects.filter(id__in=user_dept_ids)

        return all_depts, user_depts

    def get_accessible_users(self, user, organizations):
        """Get users accessible by the current user.

        Args:
            user: Current user instance.
            organizations: QuerySet of user's organizations.

        Returns:
            QuerySet of User objects within accessible organizations.
        """
        if user.is_superuser:
            return User.objects.all()

        user_org_ids = organizations.values_list('id', flat=True)
        return User.objects.filter(
            user_org_roles__organization__id__in=user_org_ids
        ).distinct()

    def get_accessible_tasks(self, user, organizations):
        """Get tasks accessible by the user.

        Only shows tasks where user is assigned user, viewer, or superuser.

        Args:
            user: Current user instance.
            organizations: QuerySet of user's organizations.

        Returns:
            QuerySet of Task objects user has explicit access to.
        """
        if user.is_superuser:
            return Task.objects.all()

        user_org_ids = organizations.values_list('id', flat=True)

        return Task.objects.filter(
            Q(organization__id__in=user_org_ids) &
            (Q(assigned_users=user) | Q(viewers=user))
        ).distinct()

    def apply_filters(self, tasks, departments, org_id, dept_id, user_id):
        """Apply URL parameter filters to querysets.

        Args:
            tasks: Task queryset.
            departments: Department queryset.
            org_id: Organization filter ID.
            dept_id: Department filter ID.
            user_id: User filter ID.

        Returns:
            Tuple of (filtered_tasks, filtered_departments).
        """
        if org_id:
            tasks = tasks.filter(organization_id=org_id)
            departments = departments.filter(organization_id=org_id)

        if dept_id:
            tasks = tasks.filter(departments__id=dept_id)

        if user_id:
            tasks = tasks.filter(
                Q(assigned_users__id=user_id) |
                Q(viewers__id=user_id)
            ).distinct()

        return tasks, departments

    def get_task_statistics(self, user):
        """Get task statistics for the current user.

        Args:
            user: Current user instance.

        Returns:
            Dictionary with task counts and completion statistics.
        """
        assigned_tasks = Task.objects.filter(assigned_users=user)
        viewer_tasks = Task.objects.filter(viewers=user)

        all_accessible = Task.objects.filter(
            Q(assigned_users=user) | Q(viewers=user)
        ).distinct()

        completed_task_ids = TaskOutput.objects.filter(
            user=user
        ).values_list('output_field__task', flat=True).distinct()

        completed_count = assigned_tasks.filter(
            id__in=completed_task_ids
        ).count()

        pending_count = assigned_tasks.exclude(
            id__in=completed_task_ids
        ).count()

        return {
            'assigned_count': assigned_tasks.count(),
            'viewer_count': viewer_tasks.count(),
            'total_accessible': all_accessible.count(),
            'completed_count': completed_count,
            'pending_count': pending_count,
        }

    def get_context_data(self, **kwargs):
        """Add dashboard statistics and filtered data to context.

        Returns:
            Dictionary with organizations, departments, users, tasks,
            and statistics filtered by user's access level.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user

        org_id = self.request.GET.get('organization')
        dept_id = self.request.GET.get('department')
        user_id = self.request.GET.get('user')

        organizations = self.get_user_organizations(user)
        all_departments, user_departments = self.get_user_departments(
            user, organizations
        )
        users = self.get_accessible_users(user, organizations)
        tasks = self.get_accessible_tasks(user, organizations)

        tasks, all_departments = self.apply_filters(
            tasks, all_departments, org_id, dept_id, user_id
        )

        task_stats = self.get_task_statistics(user)

        context.update({
            'total_organizations': organizations.count(),
            'total_departments': all_departments.count(),
            'total_users': users.count(),
            'total_tasks': tasks.count(),
            'my_assigned_tasks_count': task_stats['assigned_count'],
            'my_viewer_tasks_count': task_stats['viewer_count'],
            'completed_tasks_count': task_stats['completed_count'],
            'pending_tasks_count': task_stats['pending_count'],
            'total_accessible_tasks': task_stats['total_accessible'],
            'my_assigned_tasks': Task.objects.filter(
                assigned_users=user
            ).distinct().order_by('-created_at')[:5],
            'my_viewer_tasks': Task.objects.filter(
                viewers=user
            ).distinct().order_by('-created_at')[:5],
            'recent_tasks': tasks.order_by('-created_at')[:10],
            'organizations': organizations,
            'departments': all_departments,
            'users': users,
            'tasks': tasks,
            'user_organizations': organizations,
            'user_departments': user_departments,
            'selected_org': int(org_id) if org_id else None,
            'selected_dept': int(dept_id) if dept_id else None,
            'selected_user': int(user_id) if user_id else None,
        })

        return context
