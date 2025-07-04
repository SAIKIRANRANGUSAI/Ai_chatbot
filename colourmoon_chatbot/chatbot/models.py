from django.db import models
from django.utils import timezone

class Lead(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    service = models.CharField(max_length=100, blank=True)
    type = models.CharField(max_length=100, blank=True)
    pages = models.CharField(max_length=100, blank=True)
    cms = models.CharField(max_length=100, blank=True)
    payment = models.CharField(max_length=100, blank=True)
    budget = models.CharField(max_length=100, blank=True)
    requirement = models.TextField(blank=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    browser = models.CharField(max_length=255, null=True, blank=True, default="Unknown")
    referrer = models.CharField(max_length=255, null=True, blank=True, default="Unknown")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead from {self.name} - {self.service}"

class SupportTicket(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    domain = models.CharField(max_length=255, blank=True)
    issue = models.TextField()
    ip = models.GenericIPAddressField(blank=True, null=True)
    browser = models.CharField(max_length=255, null=True, blank=True, default="Unknown")
    referrer = models.CharField(max_length=255, null=True, blank=True, default="Unknown")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket from {self.name} - {self.domain}"