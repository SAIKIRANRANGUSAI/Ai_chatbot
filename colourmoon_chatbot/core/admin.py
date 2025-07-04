from django.contrib import admin
from .models import CustomAdmin

@admin.register(CustomAdmin)
class CustomAdminAdmin(admin.ModelAdmin):
    list_display = ['username', 'can_view_leads', 'can_view_support', 'has_dashboard_access']
    search_fields = ['username']
    list_filter = ['can_view_leads', 'can_view_support', 'has_dashboard_access']
