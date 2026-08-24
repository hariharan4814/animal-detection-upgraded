from django.contrib import admin
from apps.alerts.models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'animal_log', 'alert_type', 'status', 'created_at')
    list_filter = ('alert_type', 'status')
    search_fields = ('alert_type', 'status')
