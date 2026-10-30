import os

from django.apps import AppConfig


class MaintenanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'maintenance'
    verbose_name = 'IR Maintenance'

    def ready(self):
        from django.conf import settings
        from django.contrib import admin

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        admin.site.site_header = 'IR Maintenance'
        admin.site.site_title = 'IR Maintenance'
        admin.site.index_title = 'Catalog and records'
