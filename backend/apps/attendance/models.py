"""
Attendance model for tracking worker check-in, check-out, duration, and geolocation.
Migrated from legacy SQLite 'attendance' table.
"""

from django.db import models
from django.utils import timezone


class Attendance(models.Model):
    farmer = models.ForeignKey(
        'farmers.Farmer',
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text="Farmer associated with this attendance record"
    )
    date = models.DateField(default=timezone.now, help_text="Date of attendance record (YYYY-MM-DD)")
    check_in = models.TimeField(blank=True, null=True, help_text="Time of check-in")
    check_out = models.TimeField(blank=True, null=True, help_text="Time of check-out")
    total_hours = models.FloatField(default=0.0, blank=True, null=True, help_text="Computed duration in decimal hours")
    location = models.CharField(max_length=255, blank=True, null=True, help_text="GPS coordinates or assigned field name")
    work_description = models.TextField(blank=True, null=True, help_text="Work/task description completed during shift session entered at checkout")
    email_sent = models.BooleanField(default=False, help_text="Whether checkout summary email was sent to farmer and admin")
    email_sent_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when checkout summary email was dispatched")
    email_error = models.TextField(blank=True, null=True, help_text="Error details if email delivery failed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-check_in']
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.farmer.name} - {self.date} ({self.total_hours or 0.0} hrs)"
