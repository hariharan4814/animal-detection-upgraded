"""
Alert model representing automated notification records triggered by animal detections.
Migrated from legacy SQLite 'alerts' table.
"""

from django.db import models


class Alert(models.Model):
    animal_log = models.ForeignKey(
        'detection.AnimalLog',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='alerts',
        help_text="Animal detection log event associated with this alert"
    )
    alert_type = models.CharField(
        max_length=50,
        help_text="Notification channel: 'Email + Buzzer', 'Email', or 'Log Only'"
    )
    status = models.CharField(
        max_length=30,
        default='Triggered',
        help_text="Alert dispatch status (e.g. 'Triggered', 'Sent', 'Failed')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'

    def __str__(self):
        log_id = self.animal_log.id if self.animal_log else "None"
        return f"{self.alert_type} ({self.status}) for Log #{log_id}"
