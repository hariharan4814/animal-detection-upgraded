"""
REST API views for FarmSync Tasks Module.
Provides list, create, retrieve, update (PUT/PATCH), and delete operations with role-based access control.
"""

from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.core.responses import success_response
from apps.core.permissions import IsAdminOrReadOnly
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer


class TaskListCreateView(APIView):
    """
    GET  /api/v1/tasks/ - List all tasks with optional filters (status, assigned_to, date, start_date, end_date).
    POST /api/v1/tasks/ - Create a new task (staff/admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        queryset = Task.objects.select_related('assigned_to').all().order_by('-id')

        # Filter by status ('Pending', 'Completed')
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by assigned worker (supports 'assigned_to' and 'farmer_id')
        assigned_to_param = request.query_params.get('assigned_to') or request.query_params.get('farmer_id')
        if assigned_to_param:
            try:
                queryset = queryset.filter(assigned_to_id=int(assigned_to_param))
            except (ValueError, TypeError):
                pass

        # Filter by exact date (YYYY-MM-DD)
        date_param = request.query_params.get('date')
        if date_param:
            try:
                queryset = queryset.filter(date=date_param)
            except (DjangoValidationError, ValueError):
                pass

        # Filter by date range
        start_date = request.query_params.get('start_date')
        if start_date:
            try:
                queryset = queryset.filter(date__gte=start_date)
            except (DjangoValidationError, ValueError):
                pass

        end_date = request.query_params.get('end_date')
        if end_date:
            try:
                queryset = queryset.filter(date__lte=end_date)
            except (DjangoValidationError, ValueError):
                pass

        serializer = TaskSerializer(queryset, many=True)
        return success_response(
            message="Tasks retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        serializer = TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Task created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )


class TaskDetailView(APIView):
    """
    GET    /api/v1/tasks/{id}/ - Retrieve details of a specific task.
    PUT    /api/v1/tasks/{id}/ - Full update of a task (staff/admin only).
    PATCH  /api/v1/tasks/{id}/ - Partial update of a task (staff/admin only).
    DELETE /api/v1/tasks/{id}/ - Delete a task (staff/admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self, pk: int) -> Task:
        return get_object_or_404(Task.objects.select_related('assigned_to'), pk=pk)

    def get(self, request, pk: int, *args, **kwargs):
        task = self.get_object(pk)
        serializer = TaskSerializer(task)
        return success_response(
            message="Task details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, pk: int, *args, **kwargs):
        task = self.get_object(pk)
        serializer = TaskSerializer(task, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Task updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def patch(self, request, pk: int, *args, **kwargs):
        task = self.get_object(pk)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Task partially updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def delete(self, request, pk: int, *args, **kwargs):
        task = self.get_object(pk)
        task.delete()

        return success_response(
            message="Task deleted successfully.",
            data={},
            status_code=status.HTTP_200_OK
        )
