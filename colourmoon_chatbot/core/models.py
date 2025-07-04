from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class CustomAdmin(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    can_view_leads = models.BooleanField(default=False)
    can_view_support = models.BooleanField(default=False)
    has_dashboard_access = models.BooleanField(default=True)
    can_manage_roles = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
