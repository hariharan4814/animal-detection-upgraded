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

    # Future REST API Modular Routes (To be activated in upcoming migration steps):
    # path('api/auth/', include('apps.accounts.urls')),
    # path('api/dashboard/', include('apps.dashboard.urls')),
    # path('api/farmers/', include('apps.farmers.urls')),
    # path('api/attendance/', include('apps.attendance.urls')),
    # path('api/tasks/', include('apps.tasks.urls')),
    # path('api/detection/', include('apps.detection.urls')),
    # path('api/alerts/', include('apps.alerts.urls')),
    # path('api/settings/', include('apps.settings_app.urls')),
]

# Serve media files during local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
