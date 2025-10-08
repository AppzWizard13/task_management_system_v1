"""Organization management views.

This module contains all CRUD views for managing organizations, departments,
roles, and user role assignments with role-based permission controls and
organization-level data filtering.
"""

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
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

from .forms import RoleForm, UserOrganizationRoleForm
from .models import Department, Organization, Role, UserOrganizationRole


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


class OrganizationListView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    ListView
):
    """Display list of organizations filtered by user access.

    Requires organizations.view_organization permission.
    """

    model = Organization
    template_name = 'organizations/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10
    required_permission = 'organizations.view_organization'

    def get_context_data(self, **kwargs):
        """Add table configuration and permissions to context.

        Returns:
            Dictionary with page_title, item_name, URLs, table configuration,
            and permission keys.
        """
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
            'can_add': 'organizations.add_organization',
            'can_edit': 'organizations.change_organization',
            'can_delete': 'organizations.delete_organization',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to dashboard on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'accounts:dashboard'


class OrganizationDetailView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    DetailView
):
    """Display organization details.

    Requires organizations.view_organization permission.
    """

    model = Organization
    template_name = 'organizations/generic_detail.html'
    context_object_name = 'object'
    required_permission = 'organizations.view_organization'

    def get_context_data(self, **kwargs):
        """Add field list, permissions, and navigation URLs to context.

        Returns:
            Dictionary with fields, navigation URLs, and permissions.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Organization',
            'edit_url': 'organizations:edit',
            'list_url': 'organizations:list',
            'fields': [field for field in self.model._meta.fields],
            'can_edit': 'organizations.change_organization',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to organization list on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'organizations:list'


class OrganizationCreateView(
    LoginRequiredMixin, RolePermissionMixin, GenericFormMixin, CreateView
):
    """Create new organization with permission check.

    Requires organizations.add_organization permission.
    """

    model = Organization
    fields = ['name', 'description']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:list')
    model_name = "Organization"
    action = "Add"
    required_permission = 'organizations.add_organization'


class OrganizationUpdateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    GenericFormMixin,
    UpdateView,
):
    """Update organization with permission and access checks.

    Requires organizations.change_organization permission.
    """

    model = Organization
    fields = ['name', 'description']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:list')
    model_name = "Organization"
    action = "Edit"
    required_permission = 'organizations.change_organization'


class OrganizationDeleteView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    GenericFormMixin,
    DeleteView,
):
    """Delete organization with permission and access checks.

    Requires organizations.delete_organization permission.
    """

    model = Organization
    template_name = 'organizations/generic_confirm_delete.html'
    success_url = reverse_lazy('organizations:list')
    model_name = "Organization"
    action = "Delete"
    required_permission = 'organizations.delete_organization'


class DepartmentListView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    ListView
):
    """Display list of departments filtered by user's organizations.

    Requires organizations.view_department permission.
    """

    model = Department
    template_name = 'organizations/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10
    required_permission = 'organizations.view_department'

    def get_context_data(self, **kwargs):
        """Add table configuration and permissions to context.

        Returns:
            Dictionary with table headers, URLs, and permission keys.
        """
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
            'can_add': 'organizations.add_department',
            'can_edit': 'organizations.change_department',
            'can_delete': 'organizations.delete_department',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to dashboard on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'accounts:dashboard'


class DepartmentDetailView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    DetailView
):
    """Display department details.

    Requires organizations.view_department permission.
    """

    model = Department
    template_name = 'organizations/generic_detail.html'
    context_object_name = 'object'
    required_permission = 'organizations.view_department'

    def get_context_data(self, **kwargs):
        """Add field list, permissions, and navigation URLs to context.

        Returns:
            Dictionary with fields and navigation URLs.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Department',
            'edit_url': 'organizations:department_edit',
            'list_url': 'organizations:department_list',
            'fields': [field for field in self.model._meta.fields],
            'can_edit': 'organizations.change_department',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to department list on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'organizations:department_list'


class DepartmentCreateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFormMixin,
    GenericFormMixin,
    CreateView,
):
    """Create new department with permission check and filtered choices.

    Requires organizations.add_department permission.
    """

    model = Department
    fields = ['organization', 'name', 'description']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:department_list')
    model_name = "Department"
    action = "Add"
    required_permission = 'organizations.add_department'


class DepartmentUpdateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    OrganizationFormMixin,
    GenericFormMixin,
    UpdateView,
):
    """Update department with permission and access checks.

    Requires organizations.change_department permission.
    """

    model = Department
    fields = ['organization', 'name', 'description']
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:department_list')
    model_name = "Department"
    action = "Edit"
    required_permission = 'organizations.change_department'


class DepartmentDeleteView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    GenericFormMixin,
    DeleteView,
):
    """Delete department with permission and access checks.

    Requires organizations.delete_department permission.
    """

    model = Department
    template_name = 'organizations/generic_confirm_delete.html'
    success_url = reverse_lazy('organizations:department_list')
    model_name = "Department"
    action = "Delete"
    required_permission = 'organizations.delete_department'


class RoleListView(
    LoginRequiredMixin,
    RolePermissionMixin,
    ListView
):
    """Display list of all roles.

    Requires organizations.view_role permission.
    """

    model = Role
    template_name = 'organizations/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10
    required_permission = 'organizations.view_role'

    def get_context_data(self, **kwargs):
        """Add table configuration and permissions to context.

        Returns:
            Dictionary with table headers and permission keys.
        """
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
            'can_add': 'organizations.add_role',
            'can_edit': 'organizations.change_role',
            'can_delete': 'organizations.delete_role',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to dashboard on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'accounts:dashboard'


class RoleDetailView(
    LoginRequiredMixin,
    RolePermissionMixin,
    DetailView
):
    """Display role details including assigned permissions.

    Requires organizations.view_role permission.
    """

    model = Role
    template_name = 'organizations/role_detail.html'
    context_object_name = 'object'
    required_permission = 'organizations.view_role'

    def get_context_data(self, **kwargs):
        """Add field list, permissions, and navigation URLs to context.

        Returns:
            Dictionary with fields, role permissions, and navigation URLs.
        """
        context = super().get_context_data(**kwargs)
        role = self.get_object()

        context.update({
            'page_title': 'Role Details',
            'edit_url': 'organizations:role_edit',
            'list_url': 'organizations:role_list',
            'fields': [
                field for field in self.model._meta.fields
                if field.name != 'permissions'
            ],
            'permissions': role.permissions.all(),
            'can_edit': 'organizations.change_role',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to role list on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'organizations:role_list'


class RoleCreateView(
    LoginRequiredMixin, RolePermissionMixin, GenericFormMixin, CreateView
):
    """Create new role with permission check.

    Requires organizations.add_role permission.
    """

    model = Role
    form_class = RoleForm
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:role_list')
    model_name = "Role"
    action = "Add"
    required_permission = 'organizations.add_role'


class RoleUpdateView(
    LoginRequiredMixin, RolePermissionMixin, GenericFormMixin, UpdateView
):
    """Update role with permission check.

    Requires organizations.change_role permission.
    """

    model = Role
    form_class = RoleForm
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:role_list')
    model_name = "Role"
    action = "Edit"
    required_permission = 'organizations.change_role'


class RoleDeleteView(
    LoginRequiredMixin, RolePermissionMixin, GenericFormMixin, DeleteView
):
    """Delete role with permission check.

    Requires organizations.delete_role permission.
    """

    model = Role
    template_name = 'organizations/generic_confirm_delete.html'
    success_url = reverse_lazy('organizations:role_list')
    model_name = "Role"
    action = "Delete"
    required_permission = 'organizations.delete_role'


class UserOrganizationRoleListView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    ListView
):
    """Display list of user organization roles.

    Requires organizations.view_userorganizationrole permission.
    """

    model = UserOrganizationRole
    template_name = 'organizations/generic_list.html'
    context_object_name = 'object_list'
    paginate_by = 10
    required_permission = 'organizations.view_userorganizationrole'

    def get_context_data(self, **kwargs):
        """Add table configuration and permissions to context.

        Returns:
            Dictionary with table headers and permission keys.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'User Organization Roles',
            'item_name': 'User Organization Role',
            'add_url': 'organizations:user_org_role_add',
            'detail_url': 'organizations:user_org_role_detail',
            'edit_url': 'organizations:user_org_role_edit',
            'delete_url': 'organizations:user_org_role_delete',
            'table_headers': ['User', 'Organization', 'Role', 'Department'],
            'list_attrs': ['user', 'organization', 'role', 'department'],
            'can_add': 'organizations.add_userorganizationrole',
            'can_edit': 'organizations.change_userorganizationrole',
            'can_delete': 'organizations.delete_userorganizationrole',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to dashboard on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'accounts:dashboard'


class UserOrganizationRoleDetailView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    DetailView
):
    """Display user role assignment details including permissions.

    Requires organizations.view_userorganizationrole permission.
    """

    model = UserOrganizationRole
    template_name = 'organizations/user_org_role_detail.html'
    context_object_name = 'object'
    required_permission = 'organizations.view_userorganizationrole'

    def get_context_data(self, **kwargs):
        """Add role details, permissions, and navigation URLs to context.

        Returns:
            Dictionary with role details, permissions, and navigation URLs.
        """
        context = super().get_context_data(**kwargs)
        obj = self.get_object()

        context.update({
            'page_title': 'User Organization Role Details',
            'edit_url': 'organizations:user_org_role_edit',
            'list_url': 'organizations:user_org_role_list',
            'fields': [field for field in self.model._meta.fields],
            'permissions': obj.role.permissions.all(),
            'role_name': obj.role.name,
            'role_description': obj.role.description,
            'organization_name': obj.organization.name,
            'department_name': (
                obj.department.name if obj.department else 'No Department'
            ),
            'can_edit': 'organizations.change_userorganizationrole',
        })
        return context

    def get_permission_denied_url(self):
        """Redirect to user role list on permission denied.

        Returns:
            String URL name for redirect.
        """
        return 'organizations:user_org_role_list'


class UserOrganizationRoleCreateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFormMixin,
    GenericFormMixin,
    CreateView,
):
    """Create user role assignment with permission check and filtered choices.

    Requires organizations.add_userorganizationrole permission.
    """

    model = UserOrganizationRole
    form_class = UserOrganizationRoleForm
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:user_org_role_list')
    model_name = "User Organization Role"
    action = "Add"
    required_permission = 'organizations.add_userorganizationrole'


class UserOrganizationRoleUpdateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    OrganizationFormMixin,
    GenericFormMixin,
    UpdateView,
):
    """Update user role assignment with permission and access checks.

    Requires organizations.change_userorganizationrole permission.
    """

    model = UserOrganizationRole
    form_class = UserOrganizationRoleForm
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:user_org_role_list')
    model_name = "User Organization Role"
    action = "Edit"
    required_permission = 'organizations.change_userorganizationrole'


class UserOrganizationRoleDeleteView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFilterMixin,
    GenericFormMixin,
    DeleteView,
):
    """Delete user role assignment with permission and access checks.

    Requires organizations.delete_userorganizationrole permission.
    """

    model = UserOrganizationRole
    template_name = 'organizations/generic_confirm_delete.html'
    success_url = reverse_lazy('organizations:user_org_role_list')
    model_name = "User Organization Role"
    action = "Delete"
    required_permission = 'organizations.delete_userorganizationrole'


class UserOrganizationRoleAssignView(
    LoginRequiredMixin,
    RolePermissionMixin,
    OrganizationFormMixin,
    CreateView,
):
    """Assign role to user with custom page title and button text.

    Requires organizations.add_userorganizationrole permission.
    """

    model = UserOrganizationRole
    form_class = UserOrganizationRoleForm
    template_name = 'organizations/generic_form.html'
    success_url = reverse_lazy('organizations:user_org_role_list')
    model_name = "User Organization Role"
    action = "Assign Role"
    required_permission = 'organizations.add_userorganizationrole'

    def get_context_data(self, **kwargs):
        """Add custom page title and submit button text.

        Returns:
            Dictionary with customized page_title and submit_button.
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Assign Role to User"
        context['submit_button'] = "Assign Role"
        return context
