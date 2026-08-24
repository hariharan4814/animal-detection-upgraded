from django.contrib import admin
from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_name', 'assigned_to', 'status', 'date')
    list_filter = ('status', 'date')
    search_fields = ('task_name', 'assigned_to__name')
