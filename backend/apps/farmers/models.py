"""
Farmer model representing agricultural workforce entities.
Migrated from legacy SQLite 'farmers' table.
"""

from django.db import models


class Farmer(models.Model):
    name = models.CharField(max_length=150, help_text="Full name of the farm worker")
    phone = models.CharField(max_length=20, help_text="Contact phone number")
    field = models.CharField(max_length=150, help_text="Assigned agricultural field or work area")
    email = models.EmailField(max_length=255, blank=True, null=True, help_text="Optional worker email for attendance notifications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Farmer'
        verbose_name_plural = 'Farmers'

    def __str__(self):
        return f"{self.name} ({self.field})"
