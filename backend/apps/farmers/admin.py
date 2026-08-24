from django.contrib import admin
from apps.farmers.models import Farmer


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'field', 'email', 'created_at')
    search_fields = ('name', 'phone', 'field', 'email')
    list_filter = ('field',)
