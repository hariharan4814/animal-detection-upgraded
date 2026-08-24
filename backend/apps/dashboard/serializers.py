"""
Serializers for FarmSync Dashboard Module.
Defines explicit read-only contracts for summary metrics and activity feeds.
"""

from rest_framework import serializers


class FarmersMetricSerializer(serializers.Serializer):
    total_farmers = serializers.IntegerField(help_text="Total number of registered farm workers")


class AttendanceMetricSerializer(serializers.Serializer):
    today_attendance = serializers.IntegerField(help_text="Number of check-in records for current date")
    total_records = serializers.IntegerField(help_text="Lifetime attendance logs recorded")


class TasksMetricSerializer(serializers.Serializer):
    total_tasks = serializers.IntegerField(help_text="Total number of tasks")
    completed_tasks = serializers.IntegerField(help_text="Number of completed tasks")
    pending_tasks = serializers.IntegerField(help_text="Number of pending tasks")


class DetectionsMetricSerializer(serializers.Serializer):
    detections_today = serializers.IntegerField(help_text="Number of detections logged today")
    total_detections = serializers.IntegerField(help_text="Total lifetime detections logged")


class AlertsMetricSerializer(serializers.Serializer):
    alerts_today = serializers.IntegerField(help_text="Number of alerts triggered today")
    total_alerts = serializers.IntegerField(help_text="Total lifetime alerts")
    triggered_alerts = serializers.IntegerField(help_text="Count of alerts with status 'Triggered'")


class DashboardSummarySerializer(serializers.Serializer):
    date = serializers.CharField(help_text="Current local calculation date")
    farmers = FarmersMetricSerializer()
    attendance = AttendanceMetricSerializer()
    tasks = TasksMetricSerializer()
    detections = DetectionsMetricSerializer()
    alerts = AlertsMetricSerializer()


class RecentAlertItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    animal_type = serializers.CharField()
    alert_type = serializers.CharField()
    status = serializers.CharField()
    timestamp = serializers.CharField()


class RecentDetectionItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    animal_type = serializers.CharField()
    confidence = serializers.FloatField(allow_null=True)
    field = serializers.CharField()
    image_path = serializers.CharField()
    timestamp = serializers.CharField()


class RecentTaskItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    task_name = serializers.CharField()
    assigned_to_name = serializers.CharField()
    status = serializers.CharField()
    date = serializers.CharField()


class DashboardRecentActivitySerializer(serializers.Serializer):
    recent_alerts = serializers.ListField(child=RecentAlertItemSerializer())
    recent_detections = serializers.ListField(child=RecentDetectionItemSerializer())
    recent_tasks = serializers.ListField(child=RecentTaskItemSerializer())
