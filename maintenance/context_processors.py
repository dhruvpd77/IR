from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from .models import InventoryItem, PreventiveTask, Ticket


def nav(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    open_jobs = Ticket.objects.filter(status__in=[Ticket.Status.PENDING, Ticket.Status.ATTEMPTED])
    if user.role == user.Role.EMPLOYEE:
        open_jobs = open_jobs.filter(raised_by=user)
        low_stock = 0
    else:
        low_stock = InventoryItem.objects.filter(
            is_active=True,
            quantity__lte=F('min_quantity'),
        ).count()
    soon = timezone.localdate() + timedelta(days=7)
    pm_due = 0
    if user.is_admin_role:
        pm_due = PreventiveTask.objects.filter(completed_on__isnull=True, plan_date__lte=soon).count()
    return {
        'nav_open_count': open_jobs.count(),
        'nav_low_stock': low_stock,
        'nav_pm_due': pm_due,
    }
