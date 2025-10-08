"""Accounts URL configuration.

This module defines URL patterns for user authentication, registration,
dashboard, and user management CRUD operations.
"""

from django.urls import path

from accounts.views import (
    DashboardView,
    UserCreateView,
    UserDeleteView,
    UserDetailView,
    UserListView,
    UserLoginView,
    UserLogoutView,
    UserRegisterView,
    UserUpdateView,
)


app_name = 'accounts'


urlpatterns = [
    # Authentication and dashboard
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # User CRUD
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/add/', UserCreateView.as_view(), name='user_add'),
    path(
        'users/<int:pk>/',
        UserDetailView.as_view(),
        name='user_detail'
    ),
    path(
        'users/<int:pk>/edit/',
        UserUpdateView.as_view(),
        name='user_edit'
    ),
    path(
        'users/<int:pk>/delete/',
        UserDeleteView.as_view(),
        name='user_delete'
    ),
]
