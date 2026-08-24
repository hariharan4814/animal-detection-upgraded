from django.contrib import admin
from apps.detection.models import AnimalLog


@admin.register(AnimalLog)
class AnimalLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'animal_type', 'confidence', 'field', 'timestamp', 'image_path')
    list_filter = ('animal_type', 'field', 'timestamp')
    search_fields = ('animal_type', 'field')
