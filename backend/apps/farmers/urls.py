"""
URL routing configuration for FarmSync Farmers Module.
"""

from django.urls import path
from apps.farmers.views import FarmerListCreateView, FarmerDetailView

app_name = 'farmers'

urlpatterns = [
    path('', FarmerListCreateView.as_view(), name='farmer_list_create'),
    path('<int:pk>/', FarmerDetailView.as_view(), name='farmer_detail'),
]
