from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView,
    CreateView, UpdateView, DeleteView
)
from .models import (
    Organization, Department, Role,
    UserOrganizationRole
)
from django.contrib.auth.models import Permission


class GenericFormMixin:
    model_name = None
    action = None  # "Add", "Edit", or "Delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"{self.action} {self.model_name}"
        context['submit_button'] = "Save" if self.action in ['Add', 'Edit'] else "Confirm"
        context['success_url'] = self.success_url or reverse_lazy(
            f"{self.model._meta.app_label}:{self.model._meta.model_name}_list")
        return context


# Organization Views
class OrganizationListView(ListView):
    model = Organization
    template_name = 'organizations/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Organizations',
            'item_name': 'Organization',
            'add_url': 'organizations:add',
            'detail_url': 'organizations:detail',
            'edit_url': 'organizations:edit',
            'delete_url': 'organizations:delete',
            'table_headers': ['Name', 'Description'],
            'list_attrs': ['name', 'description'],
        })
        return context


class OrganizationDetailView(DetailView):
    model = Organization
    template_name = 'organizations/generic_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Organization',
            'edit_url': 'organizations:edit',
            'list_url': 'organizations:list',
            'fields': [field for field in self.model._meta.fields],
        })
        return context


class OrganizationCreateView(GenericFormMixin, CreateView):
    model = Organization
    fields = ['name', 'description']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:list')
    model_name = "Organization"
    action = "Add"


class OrganizationUpdateView(GenericFormMixin, UpdateView):
    model = Organization
    fields = ['name', 'description']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:list')
    model_name = "Organization"
    action = "Edit"


class OrganizationDeleteView(GenericFormMixin, DeleteView):
    model = Organization
    template_name = 'organizations/generic_confirm_delete.html'
    success_url = reverse_lazy('organizations:list')
    model_name = "Organization"
    action = "Delete"


# Department Views
class DepartmentListView(ListView):
    model = Department
    template_name = 'organizations/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Departments',
            'item_name': 'Department',
            'add_url': 'organizations:department_add',
            'detail_url': 'organizations:department_detail',
            'edit_url': 'organizations:department_edit',
            'delete_url': 'organizations:department_delete',
            'table_headers': ['Organization', 'Name', 'Description'],
            'list_attrs': ['organization', 'name', 'description'],
        })
        return context


class DepartmentDetailView(DetailView):
    model = Department
    template_name = 'organizations/generic_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Department',
            'edit_url': 'organizations:department_edit',
            'list_url': 'organizations:department_list',
            'fields': [field for field in self.model._meta.fields],
        })
        return context


class DepartmentCreateView(GenericFormMixin, CreateView):
    model = Department
    fields = ['organization', 'name', 'description']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:department_list')
    model_name = "Department"
    action = "Add"


class DepartmentUpdateView(GenericFormMixin, UpdateView):
    model = Department
    fields = ['organization', 'name', 'description']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:department_list')
    model_name = "Department"
    action = "Edit"


class DepartmentDeleteView(GenericFormMixin, DeleteView):
    model = Department
    template_name = 'organizations/generic_confirm_delete.html'
    success_url = reverse_lazy('organizations:department_list')
    model_name = "Department"
    action = "Delete"


# Role Views
class RoleListView(ListView):
    model = Role
    template_name = 'organizations/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Roles',
            'item_name': 'Role',
            'add_url': 'organizations:role_add',
            'detail_url': 'organizations:role_detail',
            'edit_url': 'organizations:role_edit',
            'delete_url': 'organizations:role_delete',
            'table_headers': ['Name', 'Description'],
            'list_attrs': ['name', 'description'],
        })
        return context


class RoleDetailView(DetailView):
    model = Role
    template_name = 'organizations/generic_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = self.get_object()
        
        context.update({
            'page_title': 'Role',
            'edit_url': 'organizations:role_edit',
            'list_url': 'organizations:role_list',
            'fields': [field for field in self.model._meta.fields if field.name != 'permissions'],
            'permissions': role.permissions.all(),  # Get all permissions for this role
        })
        return context


class RoleCreateView(GenericFormMixin, CreateView):
    model = Role
    fields = ['name', 'description', 'permissions']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:role_list')
    model_name = "Role"
    action = "Add"


class RoleUpdateView(GenericFormMixin, UpdateView):
    model = Role
    fields = ['name', 'description', 'permissions']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:role_list')
    model_name = "Role"
    action = "Edit"


class RoleDeleteView(GenericFormMixin, DeleteView):
    model = Role
    template_name = 'organizations/generic_confirm_delete.html'
    success_url = reverse_lazy('organizations:role_list')
    model_name = "Role"
    action = "Delete"


# UserOrganizationRole Views
class UserOrganizationRoleListView(ListView):
    model = UserOrganizationRole
    template_name = 'organizations/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'User Organization Roles',
            'item_name': 'User Organization Role',
            'add_url': 'organizations:user_org_role_add',
            'detail_url': 'organizations:user_org_role_detail',
            'edit_url': 'organizations:user_org_role_edit',
            'delete_url': 'organizations:user_org_role_delete',
            'table_headers': ['User', 'Organization', 'Department', 'Role'],
            'list_attrs': ['user', 'organization', 'department', 'role'],
        })
        return context


class UserOrganizationRoleDetailView(DetailView):
    model = UserOrganizationRole
    template_name = 'organizations/generic_assign_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context.update({
            'page_title': 'User Organization Role',
            'edit_url': 'organizations:user_org_role_edit',
            'list_url': 'organizations:user_org_role_list',
            'fields': [field for field in self.model._meta.fields],
            'permissions': obj.role.permissions.all(),
            'name': obj.role.name,
            'description': obj.role.description,
            'organization': obj.organization.name,
            'department': obj.department.name if obj.department else 'No Department',

        })
        return context


class UserOrganizationRoleCreateView(GenericFormMixin, CreateView):
    model = UserOrganizationRole
    fields = ['user', 'organization', 'department', 'role']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:user_org_role_list')
    model_name = "User Organization Role"
    action = "Add"


class UserOrganizationRoleUpdateView(GenericFormMixin, UpdateView):
    model = UserOrganizationRole
    fields = ['user', 'organization', 'department', 'role']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:user_org_role_list')
    model_name = "User Organization Role"
    action = "Edit"


class UserOrganizationRoleDeleteView(GenericFormMixin, DeleteView):
    model = UserOrganizationRole
    template_name = 'organizations/generic_confirm_delete.html'
    success_url = reverse_lazy('organizations:user_org_role_list')
    model_name = "User Organization Role"
    action = "Delete"






# views.py
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django import forms
from .models import UserOrganizationRole


class UserOrganizationRoleForm(forms.ModelForm):
    class Meta:
        model = UserOrganizationRole
        fields = ['user', 'organization', 'department', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionally, dynamically filter departments by selected organization via JS or override queryset here


class UserOrganizationRoleAssignView(CreateView):
    model = UserOrganizationRole
    form_class = UserOrganizationRoleForm
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:user_org_role_list')
    model_name = "User Organization Role"
    action = "Assign Role"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Assign Role to User"
        context['submit_button'] = "Assign Role"
        return context
