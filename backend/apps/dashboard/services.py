"""
Service layer for FarmSync Dashboard metrics calculation and activity aggregation.
Calculates stats on-demand from authoritative domain models with zero caching/duplicate persistence.
"""

from typing import Dict, Any, List
from django.utils import timezone

from apps.farmers.models import Farmer
from apps.attendance.models import Attendance
from apps.tasks.models import Task
from apps.detection.models import AnimalLog
from apps.alerts.models import Alert


class DashboardService:
    """
    Encapsulates all analytical calculations and aggregations for the FarmSync Dashboard.
    """

    @classmethod
    def get_summary_metrics(cls) -> Dict[str, Any]:
        """
        Computes high-level aggregated metrics across all domain modules.
        Guarantees safe zero-state values when the database is empty.
        """
        # Timezone-aware date calculations
        current_date = timezone.localdate()
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. Farmers Metrics (Legacy-derived)
        total_farmers = Farmer.objects.count()

        # 2. Attendance Metrics (Legacy-derived today_attendance + enhancement total_records)
        today_attendance = Attendance.objects.filter(date=current_date).count()
        total_attendance_records = Attendance.objects.count()

        # 3. Tasks Metrics (Legacy-derived completed_tasks + enhancements)
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status='Completed').count()
        pending_tasks = Task.objects.filter(status='Pending').count()

        # 4. Detection Vision Metrics
        detections_today = AnimalLog.objects.filter(timestamp__gte=today_start).count()
        total_detections = AnimalLog.objects.count()

        # 5. Alerts Metrics (Legacy-derived alerts_today + enhancements)
        alerts_today = Alert.objects.filter(animal_log__timestamp__gte=today_start).count()
        total_alerts = Alert.objects.count()
        triggered_alerts = Alert.objects.filter(status='Triggered').count()

        return {
            "date": str(current_date),
            "farmers": {
                "total_farmers": total_farmers,
            },
            "attendance": {
                "today_attendance": today_attendance,
                "total_records": total_attendance_records,
            },
            "tasks": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
            },
            "detections": {
                "detections_today": detections_today,
                "total_detections": total_detections,
            },
            "alerts": {
                "alerts_today": alerts_today,
                "total_alerts": total_alerts,
                "triggered_alerts": triggered_alerts,
            }
        }

    @classmethod
    def get_recent_activity(cls, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves the latest records across Alerts, Animal Detections, and Tasks.
        """
        safe_limit = max(1, min(limit, 20))

        # Recent Alerts (Joined with AnimalLog)
        recent_alerts_qs = Alert.objects.select_related('animal_log').all().order_by('-id')[:safe_limit]
        recent_alerts = []
        for alert in recent_alerts_qs:
            recent_alerts.append({
                "id": alert.id,
                "animal_type": alert.animal_log.animal_type if alert.animal_log else "Unknown",
                "alert_type": alert.alert_type,
                "status": alert.status,
                "timestamp": alert.animal_log.timestamp.isoformat() if (alert.animal_log and alert.animal_log.timestamp) else alert.created_at.isoformat()
            })

        # Recent Vision Detections
        recent_detections_qs = AnimalLog.objects.all().order_by('-timestamp')[:safe_limit]
        recent_detections = []
        for log in recent_detections_qs:
            recent_detections.append({
                "id": log.id,
                "animal_type": log.animal_type,
                "confidence": round(log.confidence, 2) if log.confidence is not None else None,
                "field": log.field,
                "image_path": log.image_path,
                "timestamp": log.timestamp.isoformat() if log.timestamp else log.created_at.isoformat()
            })

        # Recent Task Assignments (Joined with Farmer)
        recent_tasks_qs = Task.objects.select_related('assigned_to').all().order_by('-id')[:safe_limit]
        recent_tasks = []
        for task in recent_tasks_qs:
            recent_tasks.append({
                "id": task.id,
                "task_name": task.task_name,
                "assigned_to_name": task.assigned_to.name if task.assigned_to else "Unassigned",
                "status": task.status,
                "date": str(task.date)
            })

        return {
            "recent_alerts": recent_alerts,
            "recent_detections": recent_detections,
            "recent_tasks": recent_tasks,
        }
