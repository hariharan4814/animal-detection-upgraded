"""
URL configuration for FarmSync backend project.

Root routing gateway for FarmSync / Intelligent Animal Detection System.
Phase: STEP 1 - Project Foundation.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin Panel
    path('admin/', admin.site.urls),

    # Version 1 REST API Global Gateway
    path('api/v1/', include('apps.core.urls')),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/settings/', include('apps.settings_app.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
    path('api/v1/farmers/', include('apps.farmers.urls')),
    path('api/v1/attendance/', include('apps.attendance.urls')),

    path('api/v1/tasks/', include('apps.tasks.urls')),

    path('api/v1/detection/', include('apps.detection.urls')),

    # Future REST API Modular Routes (To be activated in upcoming migration steps):
    # path('api/v1/alerts/', include('apps.alerts.urls')),
]

# Serve media files during local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
