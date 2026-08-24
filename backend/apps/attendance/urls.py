"""
URL routing configuration for FarmSync Attendance Module.
"""

from django.urls import path
from apps.attendance.views import (
    AttendanceListView,
    AttendanceDetailView,
    CheckInView,
    CheckOutView,
    AttendanceReportView,
)

app_name = 'attendance'

urlpatterns = [
    path('', AttendanceListView.as_view(), name='attendance_list'),
    path('<int:pk>/', AttendanceDetailView.as_view(), name='attendance_detail'),
    path('check-in/', CheckInView.as_view(), name='check_in'),
    path('check-out/', CheckOutView.as_view(), name='check_out'),
    path('report/', AttendanceReportView.as_view(), name='attendance_report'),
]
