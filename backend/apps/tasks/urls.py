"""
URL routing configuration for FarmSync Tasks Module.
"""

from django.urls import path
from apps.tasks.views import TaskListCreateView, TaskDetailView

app_name = 'tasks'

urlpatterns = [
    path('', TaskListCreateView.as_view(), name='task_list_create'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task_detail'),
]
