from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.contrib import messages
from django.db import IntegrityError
from datetime import timedelta
import json
import logging
from django.core.paginator import Paginator
from chatbot.models import Lead, SupportTicket
from .models import CustomAdmin

# Set up logging
logger = logging.getLogger(__name__)

# --------------------------
# Session Auth Helpers
# --------------------------

def get_logged_in_admin(request):
    admin_id = request.session.get('admin_user_id')
    if not admin_id:
        return None
    try:
        return CustomAdmin.objects.get(id=admin_id)
    except CustomAdmin.DoesNotExist:
        return None

# --------------------------
# Authentication Views
# --------------------------

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = CustomAdmin.objects.get(username=username)
            if not user.check_password(password):
                raise CustomAdmin.DoesNotExist
            request.session['admin_user_id'] = user.id
            return redirect('/core/dashboard/')
        except CustomAdmin.DoesNotExist:
            logger.warning(f"Failed login attempt for username: {username}")
            return render(request, "core/login.html", {
                "error": "Invalid username or password"
            })

    return render(request, "core/login.html")

def logout_view(request):
    request.session.flush()
    return redirect('/core/login/')

# --------------------------
# Dashboard View
# --------------------------

def dashboard(request):
    admin_user = get_logged_in_admin(request)
    if not admin_user:
        return redirect('/core/login/')
    if not admin_user.has_dashboard_access:
        logger.warning(f"Access denied for user {admin_user.username} to dashboard")
        return HttpResponse("Access denied", status=403)

    now = timezone.localtime(timezone.now())
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Accurate "Today" counts using datetime range
    leads_today = Lead.objects.filter(created_at__range=(start_of_today, end_of_today)).count()

    support_today = SupportTicket.objects.filter(created_at__range=(start_of_today, end_of_today)).count()

    def get_last_7_days_counts(model):
        days = []
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            count = model.objects.filter(created_at__range=(start, end)).count()
            days.append({
                "date": day.strftime("%Y-%m-%d"),
                "count": count
            })
        return days

    lead_data = get_last_7_days_counts(Lead)
    support_data = get_last_7_days_counts(SupportTicket)

    return render(request, 'core/dashboard.html', {
        'leads_today': leads_today,
        'total_leads': Lead.objects.count(),
        'support_today': support_today,
        'total_support': SupportTicket.objects.count(),
        'lead_data': json.dumps(lead_data),
        'support_data': json.dumps(support_data),
        'admin_user': admin_user,
        'recent_leads': Lead.objects.order_by('-created_at')[:5],
        'recent_supports': SupportTicket.objects.order_by('-created_at')[:5],
    })


# --------------------------
# Leads and Support Views
# --------------------------

def leads_table(request):
    admin_user = get_logged_in_admin(request)
    if not admin_user:
        return redirect('/core/login/')
    if not admin_user.can_view_leads:
        logger.warning(f"Access denied for user {admin_user.username} to leads table")
        return HttpResponse("Access denied", status=403)

    leads_list = Lead.objects.all().order_by('-created_at')
    paginator = Paginator(leads_list, 10)  # 10 leads per page
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)

    return render(request, "core/leads_table.html", {
        "leads": leads,
        "admin_user": admin_user
    })

def support_table(request):
    admin_user = get_logged_in_admin(request)
    if not admin_user:
        return redirect('/core/login/')
    if not admin_user.can_view_support:
        logger.warning(f"Access denied for user {admin_user.username} to support table")
        return HttpResponse("Access denied", status=403)

    tickets_list = SupportTicket.objects.all().order_by('-created_at')
    paginator = Paginator(tickets_list, 10)  # 10 tickets per page
    page_number = request.GET.get('page')
    tickets = paginator.get_page(page_number)

    return render(request, "core/support_table.html", {
        "tickets": tickets,
        "admin_user": admin_user
    })

# --------------------------
# Admin Role Management Views
# --------------------------

def admin_roles_view(request):
    admin_user = get_logged_in_admin(request)
    if not admin_user:
        return redirect('/core/login/')
    if not admin_user.can_manage_roles:
        logger.warning(f"Access denied for user {admin_user.username} to admin roles")
        return HttpResponse("Access denied", status=403)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        can_view_leads = 'can_view_leads' in request.POST
        can_view_support = 'can_view_support' in request.POST
        has_dashboard_access = 'has_dashboard_access' in request.POST
        can_manage_roles = 'can_manage_roles' in request.POST

        if not username or not password:
            messages.error(request, "Username and password are required.")
        else:
            try:
                new_admin = CustomAdmin(
                    username=username,
                    can_view_leads=can_view_leads,
                    can_view_support=can_view_support,
                    has_dashboard_access=has_dashboard_access,
                    can_manage_roles=can_manage_roles,
                )
                new_admin.set_password(password)
                new_admin.save()
                messages.success(request, f"Sub-admin '{username}' created successfully.")
            except IntegrityError:
                messages.error(request, "Username already exists.")

    admins = CustomAdmin.objects.all().order_by('-id')
    return render(request, "core/admin_roles.html", {
        "admins": admins,
        "admin_user": admin_user
    })

def update_admin_role(request, admin_id):
    admin_user = get_logged_in_admin(request)
    if not admin_user:
        return redirect('/core/login/')
    if not admin_user.can_manage_roles:
        logger.warning(f"Access denied for user {admin_user.username} to update admin role")
        return HttpResponse("Access denied", status=403)

    try:
        target = CustomAdmin.objects.get(id=admin_id)
    except CustomAdmin.DoesNotExist:
        logger.error(f"Admin not found: {admin_id}")
        return HttpResponse("Admin not found", status=404)

    if request.method == 'POST':
        target.has_dashboard_access = 'has_dashboard_access' in request.POST
        target.can_view_leads = 'can_view_leads' in request.POST
        target.can_view_support = 'can_view_support' in request.POST
        target.can_manage_roles = 'can_manage_roles' in request.POST
        target.save()
        messages.success(request, f"Admin '{target.username}' updated successfully.")
        return redirect('/core/admin/roles/')

    return render(request, "core/edit_admin_role.html", {
        "admin": target,
        "admin_user": admin_user
    })

# --------------------------
# Change Password View
# --------------------------

def change_password_view(request):
    admin_user = get_logged_in_admin(request)
    if not admin_user:
        return redirect('/core/login/')

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not admin_user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            admin_user.set_password(new_password)
            admin_user.save()
            messages.success(request, "Password changed successfully.")
            return redirect('/core/change-password/')

    return render(request, "core/change_password.html", {
        "admin_user": admin_user
    })