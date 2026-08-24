from django.contrib import admin
from apps.attendance.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'farmer', 'date', 'check_in', 'check_out', 'total_hours', 'location')
    list_filter = ('date', 'farmer')
    search_fields = ('farmer__name', 'location')
