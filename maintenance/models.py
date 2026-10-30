import os

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


def format_duration(delta):
    if delta is None:
        return '—'
    total = int(abs(delta.total_seconds()))
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    if days:
        return f'{days}d {hours:02d}h {minutes:02d}m'
    return f'{hours:02d}h {minutes:02d}m {seconds:02d}s'


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Super Admin'
        ADMIN = 'admin', 'Admin'
        EMPLOYEE = 'employee', 'Employee'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    employee_code = models.CharField(max_length=20, unique=True, blank=True)
    department = models.CharField(max_length=80, blank=True)
    phone = models.CharField('Extension', max_length=30, blank=True)
    created_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='provisioned_users',
    )

    class Meta:
        ordering = ['first_name', 'username']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN

    @property
    def is_admin_role(self):
        return self.role in {self.Role.SUPERADMIN, self.Role.ADMIN}

    def save(self, *args, **kwargs):
        if not self.employee_code:
            self.employee_code = self._next_code()
        super().save(*args, **kwargs)

    def _next_code(self):
        prefix = {
            self.Role.SUPERADMIN: 'SA',
            self.Role.ADMIN: 'ADM',
            self.Role.EMPLOYEE: 'EMP',
        }.get(self.role, 'EMP')
        numbers = []
        for code in User.objects.filter(employee_code__startswith=f'{prefix}-').values_list('employee_code', flat=True):
            tail = str(code).rsplit('-', 1)[-1]
            if tail.isdigit():
                numbers.append(int(tail))
        return f'{prefix}-{max(numbers, default=100) + 1:03d}'


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='subcategories')
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=24, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'subcategories'
        constraints = [
            models.UniqueConstraint(fields=['category', 'name'], name='uniq_subcategory_name'),
        ]

    def __str__(self):
        return f'{self.category.name} · {self.name}'


class Asset(models.Model):
    subcategory = models.ForeignKey(SubCategory, on_delete=models.PROTECT, related_name='assets')
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=140)
    location = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} · {self.name}'


class Ticket(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Received'
        ATTEMPTED = 'attempted', 'Accepted'
        COMPLETED = 'completed', 'Done'
        REJECTED = 'rejected', 'Rejected'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    ticket_no = models.CharField(max_length=32, unique=True)
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='tickets')
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='tickets')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='tickets')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.PROTECT, related_name='tickets')
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    remarks = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    attempted_at = models.DateTimeField(null=True, blank=True)
    attempted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='attempted_tickets',
    )
    attempt_notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='completed_tickets',
    )
    completion_notes = models.TextField(blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='rejected_tickets',
    )
    reject_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return self.ticket_no

    def get_absolute_url(self):
        return reverse('ticket_detail', args=[self.pk])

    @property
    def is_open(self):
        return self.status in {self.Status.PENDING, self.Status.ATTEMPTED}

    @property
    def idle_delta(self):
        """Machine idle time starts when an admin accepts the request."""
        if not self.attempted_at:
            return None
        end = self.completed_at or timezone.now()
        return end - self.attempted_at

    @property
    def idle_display(self):
        if self.idle_delta is None:
            return 'Not started'
        return format_duration(self.idle_delta)

    @property
    def idle_is_critical(self):
        if self.status != self.Status.ATTEMPTED or self.idle_delta is None:
            return False
        return self.idle_delta.total_seconds() >= 8 * 3600

    @property
    def response_display(self):
        if not self.attempted_at:
            return None
        return format_duration(self.attempted_at - self.created_at)

    @property
    def repair_display(self):
        if not self.attempted_at or not self.completed_at:
            return None
        return format_duration(self.completed_at - self.attempted_at)


class TicketMedia(models.Model):
    VIDEO_EXT = {'.mp4', '.webm', '.mov', '.mkv', '.avi'}

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='tickets/%Y/%m/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='uploads',
    )
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return os.path.basename(self.file.name)

    @property
    def is_video(self):
        ext = os.path.splitext(self.file.name)[1].lower()
        return ext in self.VIDEO_EXT


class InventoryItem(models.Model):
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, default='pcs')
    quantity = models.PositiveIntegerField(default=0)
    min_quantity = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.sku} · {self.name}'

    @property
    def is_low(self):
        return self.quantity <= self.min_quantity

    @property
    def stock_ratio(self):
        if self.min_quantity <= 0:
            return 100
        return min(100, round(self.quantity / self.min_quantity * 100))


class StockMovement(models.Model):
    class Reason(models.TextChoices):
        JOB = 'job', 'Used on job'
        RECEIPT = 'receipt', 'Stock received'
        ADJUST = 'adjust', 'Adjustment'

    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='movements')
    ticket = models.ForeignKey(Ticket, null=True, blank=True, on_delete=models.SET_NULL, related_name='movements')
    quantity_change = models.IntegerField()
    balance_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=20, choices=Reason.choices)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='stock_movements',
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.item.sku} {self.quantity_change:+d}'

    @property
    def used_quantity(self):
        return abs(self.quantity_change)


class PreventiveTask(models.Model):
    """One planned preventive visit. The next visit is created after this one is completed."""

    value_stream = models.CharField(max_length=80)
    equipment_name = models.CharField(max_length=160)
    asset_name = models.CharField(max_length=200, blank=True)
    asset_number = models.CharField(max_length=40, blank=True)
    location = models.CharField(max_length=120)
    frequency = models.CharField(max_length=8)
    frequency_months = models.PositiveSmallIntegerField(default=3)
    schedule_month = models.CharField(max_length=20, blank=True)
    plan_date = models.DateField()
    completed_on = models.DateField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='completed_preventive',
    )
    vendor_name = models.CharField(max_length=120, blank=True)
    work_type = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['plan_date', 'value_stream', 'equipment_name']
        constraints = [
            models.UniqueConstraint(
                fields=['asset_number', 'equipment_name', 'location', 'plan_date'],
                name='uniq_preventive_visit',
            ),
        ]

    def __str__(self):
        return f'{self.equipment_name} · {self.plan_date}'

    @property
    def is_done(self):
        return self.completed_on is not None

    @property
    def days_until(self):
        return (self.plan_date - timezone.localdate()).days

    @property
    def is_overdue(self):
        return not self.is_done and self.days_until < 0

    @property
    def is_reminder(self):
        return not self.is_done and self.days_until <= 7

    @property
    def reminder_label(self):
        if self.is_done:
            return ''
        days = self.days_until
        if days < 0:
            return f'Overdue by {-days} days'
        if days == 0:
            return 'Due today'
        if days <= 7:
            return f'Reminder · due in {days} days'
        return ''

    @property
    def is_external(self):
        return self.work_type.lower().startswith('external')

    @property
    def vendor_display(self):
        if self.is_external and self.vendor_name:
            return self.vendor_name
        return ''

    @property
    def frequency_label(self):
        if self.frequency_months == 12:
            return 'Every 12 months'
        if self.frequency_months == 1:
            return 'Every month'
        return f'Every {self.frequency_months} months'
