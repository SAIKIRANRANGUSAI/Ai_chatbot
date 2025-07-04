from django.contrib import admin
from .models import Lead, SupportTicket

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "service", "created_at")
    search_fields = ("name", "email", "service")
    readonly_fields = ("ip", "browser", "referrer", "created_at")

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "domain", "created_at")
    search_fields = ("name", "domain", "issue")
    readonly_fields = ("ip", "browser", "referrer", "created_at")
