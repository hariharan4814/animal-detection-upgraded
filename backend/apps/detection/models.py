"""
AnimalLog model representing camera animal detection events.
Migrated from legacy SQLite 'animal_logs' table.
"""

from django.db import models
from django.utils import timezone


class AnimalLog(models.Model):
    animal_type = models.CharField(max_length=100, help_text="Detected animal species (e.g. lion, deer, wolf)")
    confidence = models.FloatField(blank=True, null=True, help_text="Model confidence score between 0.0 and 1.0")
    timestamp = models.DateTimeField(default=timezone.now, help_text="Detection event timestamp")
    field = models.CharField(max_length=150, default='Main Field', help_text="Camera field location")
    image_path = models.CharField(max_length=255, help_text="Relative storage path to captured snapshot image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Animal Detection Log'
        verbose_name_plural = 'Animal Detection Logs'

    def __str__(self):
        conf_str = f" ({self.confidence:.2f})" if self.confidence is not None else ""
        return f"{self.animal_type.capitalize()}{conf_str} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
