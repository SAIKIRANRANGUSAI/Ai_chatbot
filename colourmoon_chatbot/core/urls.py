from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/leads/", views.leads_table, name="leads"),
    path("dashboard/support/", views.support_table, name="support"),
    path("change-password/", views.change_password_view, name="change_password"),
    path("admin/roles/", views.admin_roles_view, name="admin_roles"),
    path("admin/roles/<int:admin_id>/edit/", views.update_admin_role, name="edit_admin_role"),
]
