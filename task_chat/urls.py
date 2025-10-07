# task_chat/urls.py

from django.urls import path
from . import views

app_name = 'task_chat'

urlpatterns = [
    path('<int:task_id>/', views.task_chat_view, name='chat'),
]
