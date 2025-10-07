# tasks/urls.py
from django.urls import path
from .views import (
    # Task views
    TaskListView,
    TaskDetailView,
    TaskCreateView,
    TaskUpdateView,
    TaskDeleteView,
    # Task Output Field views
    TaskOutputFieldListView,
    TaskOutputFieldDetailView,
    TaskOutputFieldCreateView,
    TaskOutputFieldUpdateView,
    TaskOutputFieldDeleteView,
    # Task Output views
    TaskOutputListView,
    TaskOutputDetailView,
    TaskOutputCreateView,
    TaskOutputUpdateView,
    TaskOutputDeleteView,
    # User-specific task views
    MyAssignedTasksListView,
    MyViewerTasksListView,
    get_organization_data,
    TaskCompletionView,
)


app_name = 'tasks'


urlpatterns = [
    # Task CRUD
    path('', TaskListView.as_view(), name='task_list'),
    path('add/', TaskCreateView.as_view(), name='task_add'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task_detail'),
    path('<int:pk>/edit/', TaskUpdateView.as_view(), name='task_edit'),
    path('<int:pk>/delete/', TaskDeleteView.as_view(), name='task_delete'),

    # Task Output Field CRUD
    path('output-fields/', TaskOutputFieldListView.as_view(), name='task_output_field_list'),
    path('output-fields/add/', TaskOutputFieldCreateView.as_view(), name='task_output_field_add'),
    path('output-fields/<int:pk>/', TaskOutputFieldDetailView.as_view(), name='task_output_field_detail'),
    path('output-fields/<int:pk>/edit/', TaskOutputFieldUpdateView.as_view(), name='task_output_field_edit'),
    path('output-fields/<int:pk>/delete/', TaskOutputFieldDeleteView.as_view(), name='task_output_field_delete'),

    # Task Output CRUD (User Submissions)
    path('outputs/', TaskOutputListView.as_view(), name='task_output_list'),
    path('outputs/add/', TaskOutputCreateView.as_view(), name='task_output_add'),
    path('outputs/<int:pk>/', TaskOutputDetailView.as_view(), name='task_output_detail'),
    path('outputs/<int:pk>/edit/', TaskOutputUpdateView.as_view(), name='task_output_edit'),
    path('outputs/<int:pk>/delete/', TaskOutputDeleteView.as_view(), name='task_output_delete'),

    # User-specific task views
    path('my-tasks/', MyAssignedTasksListView.as_view(), name='my_assigned_tasks'),
    path('my-viewer-tasks/', MyViewerTasksListView.as_view(), name='my_viewer_tasks'),


    path('api/organization/<int:org_id>/data/', get_organization_data, name='get_organization_data'),
    path('<int:pk>/complete/', TaskCompletionView.as_view(), name='task_complete'),
]
