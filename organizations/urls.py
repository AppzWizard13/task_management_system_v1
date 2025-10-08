"""Organization management URL configuration.

This module defines URL patterns for organization, department, role,
and user role assignment CRUD operations.
"""

from django.urls import path

from . import views


app_name = 'organizations'


urlpatterns = [
    # Organization URLs
    path('', views.OrganizationListView.as_view(), name='list'),
    path('add/', views.OrganizationCreateView.as_view(), name='add'),
    path(
        '<int:pk>/',
        views.OrganizationDetailView.as_view(),
        name='detail'
    ),
    path(
        '<int:pk>/edit/',
        views.OrganizationUpdateView.as_view(),
        name='edit'
    ),
    path(
        '<int:pk>/delete/',
        views.OrganizationDeleteView.as_view(),
        name='delete'
    ),

    # Department URLs
    path(
        'departments/',
        views.DepartmentListView.as_view(),
        name='department_list'
    ),
    path(
        'departments/add/',
        views.DepartmentCreateView.as_view(),
        name='department_add'
    ),
    path(
        'departments/<int:pk>/',
        views.DepartmentDetailView.as_view(),
        name='department_detail'
    ),
    path(
        'departments/<int:pk>/edit/',
        views.DepartmentUpdateView.as_view(),
        name='department_edit'
    ),
    path(
        'departments/<int:pk>/delete/',
        views.DepartmentDeleteView.as_view(),
        name='department_delete'
    ),

    # Role URLs
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/add/', views.RoleCreateView.as_view(), name='role_add'),
    path(
        'roles/<int:pk>/',
        views.RoleDetailView.as_view(),
        name='role_detail'
    ),
    path(
        'roles/<int:pk>/edit/',
        views.RoleUpdateView.as_view(),
        name='role_edit'
    ),
    path(
        'roles/<int:pk>/delete/',
        views.RoleDeleteView.as_view(),
        name='role_delete'
    ),

    # User Organization Role URLs
    path(
        'user-org-roles/',
        views.UserOrganizationRoleListView.as_view(),
        name='user_org_role_list'
    ),
    path(
        'user-org-roles/add/',
        views.UserOrganizationRoleCreateView.as_view(),
        name='user_org_role_add'
    ),
    path(
        'user-org-roles/assign/',
        views.UserOrganizationRoleAssignView.as_view(),
        name='user_org_role_assign'
    ),
    path(
        'user-org-roles/<int:pk>/',
        views.UserOrganizationRoleDetailView.as_view(),
        name='user_org_role_detail'
    ),
    path(
        'user-org-roles/<int:pk>/edit/',
        views.UserOrganizationRoleUpdateView.as_view(),
        name='user_org_role_edit'
    ),
    path(
        'user-org-roles/<int:pk>/delete/',
        views.UserOrganizationRoleDeleteView.as_view(),
        name='user_org_role_delete'
    ),
]
