"""
Task model for tracking work assignments delegated to farm workers.
Migrated from legacy SQLite 'tasks' table.
"""

from django.db import models
from django.utils import timezone


class Task(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    ]

    task_name = models.CharField(max_length=255, help_text="Description of the assigned farm task")
    assigned_to = models.ForeignKey(
        'farmers.Farmer',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tasks',
        help_text="Farmer assigned to this task"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Task completion status"
    )
    date = models.DateField(default=timezone.now, help_text="Date when the task was assigned")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        assignee = self.assigned_to.name if self.assigned_to else "Unassigned"
        return f"{self.task_name} -> {assignee} [{self.status}]"
