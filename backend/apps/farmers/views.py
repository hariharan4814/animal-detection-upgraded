"""
REST API views for FarmSync Farmers Module.
Provides full CRUD capabilities with role-based access control and standardized responses.
"""

from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.core.responses import success_response
from apps.core.permissions import IsAdminOrReadOnly
from apps.farmers.models import Farmer
from apps.farmers.serializers import FarmerSerializer


class FarmerListCreateView(APIView):
    """
    GET  /api/v1/farmers/ - List all registered farmers in deterministic alphabetical order.
    POST /api/v1/farmers/ - Register a new farm worker (staff/admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        farmers = Farmer.objects.all().order_by('name', 'id')
        serializer = FarmerSerializer(farmers, many=True)
        return success_response(
            message="Farmers retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        serializer = FarmerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Farmer created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )


class FarmerDetailView(APIView):
    """
    GET    /api/v1/farmers/{id}/ - Retrieve details of a specific farmer.
    PUT    /api/v1/farmers/{id}/ - Full update of a farmer record (staff/admin only).
    PATCH  /api/v1/farmers/{id}/ - Partial update of a farmer record (staff/admin only).
    DELETE /api/v1/farmers/{id}/ - Delete a farmer record (staff/admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self, pk: int) -> Farmer:
        return get_object_or_404(Farmer, pk=pk)

    def get(self, request, pk: int, *args, **kwargs):
        farmer = self.get_object(pk)
        serializer = FarmerSerializer(farmer)
        return success_response(
            message="Farmer details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, pk: int, *args, **kwargs):
        farmer = self.get_object(pk)
        serializer = FarmerSerializer(farmer, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Farmer updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def patch(self, request, pk: int, *args, **kwargs):
        farmer = self.get_object(pk)
        serializer = FarmerSerializer(farmer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Farmer partially updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def delete(self, request, pk: int, *args, **kwargs):
        farmer = self.get_object(pk)
        farmer.delete()

        return success_response(
            message="Farmer deleted successfully.",
            data={},
            status_code=status.HTTP_200_OK
        )
