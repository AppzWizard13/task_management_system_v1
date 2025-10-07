from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.shortcuts import redirect
from django.contrib.auth.forms import UserCreationForm

from tasks.models import Task

class UserLoginView(LoginView):
    template_name = 'accounts/login.html'  # Create this template
    redirect_authenticated_user = True

class UserRegisterView(FormView):
    template_name = 'accounts/register.html'  # Create this template
    form_class = UserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)

class UserLogoutView(LogoutView):
    template_name = 'accounts/logout.html'  # Optional confirmation page
    next_page = reverse_lazy('login')


from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView,
    CreateView, UpdateView, DeleteView
)
from accounts.models import CustomUser


class GenericFormMixin:
    model_name = None
    action = None  # "Add", "Edit", or "Delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"{self.action} {self.model_name}"
        context['submit_button'] = "Save" if self.action in ['Add', 'Edit'] else "Confirm"
        context['success_url'] = self.success_url or reverse_lazy(
            f"{self.model._meta.app_label}:{self.model._meta.model_name}_list"
        )
        return context


class UserListView(ListView):
    model = CustomUser
    template_name = 'accounts/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Users',
            'item_name': 'User',
            'add_url': 'user_add',
            'detail_url': 'user_detail',
            'edit_url': 'user_edit',
            'delete_url': 'user_delete',
            'table_headers': ['Username', 'Email', 'Phone Number'],
            'list_attrs': ['username', 'email', 'phone_number'],
        })
        return context


class UserDetailView(DetailView):
    model = CustomUser
    template_name = 'accounts/generic_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'User',
            'edit_url': 'user_edit',
            'list_url': 'user_list',
            'fields': [field for field in self.model._meta.fields],
        })
        return context


class UserCreateView(GenericFormMixin, CreateView):
    model = CustomUser
    fields = ['username', 'email', 'phone_number', 'password']
    template_name = 'accounts/generic_form.html'
    success_url = reverse_lazy('user_list')
    model_name = "User"
    action = "Add"


class UserUpdateView(GenericFormMixin, UpdateView):
    model = CustomUser
    fields = ['username', 'email', 'phone_number']
    template_name = 'accounts/generic_form.html'
    success_url = reverse_lazy('user_list')
    model_name = "User"
    action = "Edit"


class UserDeleteView(GenericFormMixin, DeleteView):
    model = CustomUser
    template_name = 'accounts/generic_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    model_name = "User"
    action = "Delete"





from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from organizations.models import Organization, Department, UserOrganizationRole
from tasks.models import Task
from django.contrib.auth import get_user_model
from django.db.models import Q, Count

User = get_user_model()

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    login_url = '/login/'
    redirect_field_name = 'next'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Filters from GET params
        org_id = self.request.GET.get('organization')
        dept_id = self.request.GET.get('department')
        user_id = self.request.GET.get('user')

        # If superuser, show all data; else filter by user's organizations
        if user.is_superuser:
            organizations = Organization.objects.all()
            departments = Department.objects.all()
            users = User.objects.all()
            tasks = Task.objects.all()
            user_organizations = organizations
            user_departments = departments
        else:
            # Get organizations user belongs to
            user_org_roles = UserOrganizationRole.objects.filter(user=user).select_related('organization', 'department')
            user_orgs = user_org_roles.values_list('organization', flat=True).distinct()
            
            organizations = Organization.objects.filter(id__in=user_orgs)
            user_organizations = organizations  # User's organizations for display
            
            # Get departments within those organizations
            departments = Department.objects.filter(organization__in=user_orgs)
            
            # Get user's specific departments
            user_dept_ids = user_org_roles.filter(department__isnull=False).values_list('department', flat=True).distinct()
            user_departments = Department.objects.filter(id__in=user_dept_ids)
            
            # Get users within those organizations
            users = User.objects.filter(user_org_roles__organization__in=user_orgs).distinct()
            
            # Get tasks: assigned to user OR user is viewer OR within user's organizations
            tasks = Task.objects.filter(
                Q(assigned_users=user) |
                Q(viewers=user) |
                Q(organization__in=user_orgs)
            ).distinct()

        # Apply filters
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

        # Statistics
        context['total_organizations'] = organizations.count()
        context['total_departments'] = departments.count()
        context['total_users'] = users.count()
        context['total_tasks'] = tasks.count()

        # My tasks for current user
        context['my_assigned_tasks'] = Task.objects.filter(assigned_users=user).distinct()[:5]
        context['my_viewer_tasks'] = Task.objects.filter(viewers=user).distinct()[:5]

        # Recent tasks (all accessible tasks)
        context['recent_tasks'] = tasks.order_by('-created_at')[:10]

        # Lists for filters
        context['organizations'] = organizations
        context['departments'] = departments
        context['users'] = users
        context['tasks'] = tasks

        # User's specific organizations and departments
        context['user_organizations'] = user_organizations
        context['user_departments'] = user_departments

        # Selected filters
        context['selected_org'] = int(org_id) if org_id else None
        context['selected_dept'] = int(dept_id) if dept_id else None
        context['selected_user'] = int(user_id) if user_id else None

        return context

