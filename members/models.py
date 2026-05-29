import datetime
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


class User(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('member', 'Member')]

    email = models.EmailField(max_length=254, unique=True)
    password_hash = models.CharField(max_length=256)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    failed_login_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def increment_failed(self, ip_address=None):
        self.failed_login_count += 1
        if self.failed_login_count >= 5:
            self.locked_until = timezone.now() + datetime.timedelta(minutes=15)
        self.save(update_fields=['failed_login_count', 'locked_until'])
        # Log the failed attempt with timestamp and IP (NFR-S06)
        FailedLoginLog.objects.create(
            account_identifier=self.email,
            ip_address=ip_address or '',
        )

    def reset_failed(self):
        self.failed_login_count = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_count', 'locked_until'])

    def __str__(self):
        return f"{self.email} ({self.role})"


class FailedLoginLog(models.Model):
    account_identifier = models.CharField(max_length=254)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.account_identifier} @ {self.ip_address} — {self.timestamp}"


class Member(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Expiring Soon', 'Expiring Soon'),
        ('Expired', 'Expired'),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, unique=True)
    contact = models.CharField(max_length=20)
    plan = models.ForeignKey(
        'core.MembershipPlan',
        on_delete=models.PROTECT,
        related_name='members',
    )
    start_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='member_profile',
    )

    def compute_status(self):
        """
        BR-01: Active — has checked in within the last 7 days and membership not expired.
        BR-02: Inactive — no check-in for more than 7 days and membership not expired.
        BR-03: Expiring Soon — expiry within 7 days.
        BR-04: Expired — expiry_date < today.
        """
        today = timezone.localdate()

        if self.expiry_date < today:
            return 'Expired'

        days_left = (self.expiry_date - today).days
        if days_left <= 7:
            return 'Expiring Soon'

        last = self.last_checkin()
        if last is None or (today - last).days > 7:
            return 'Inactive'

        return 'Active'

    def days_remaining(self):
        today = timezone.localdate()
        return max(0, (self.expiry_date - today).days)

    def last_checkin(self):
        log = self.attendance_logs.order_by('-check_in_date', '-check_in_time').first()
        return log.check_in_date if log else None

    def is_newly_inactive(self):
        """
        Returns True if this member is Inactive and no inactivity_alert
        NotificationLog has been created since the last check-in (or ever).
        Prevents duplicate alerts per inactivity period.
        """
        if self.status != 'Inactive':
            return False

        last = self.last_checkin()
        qs = self.notification_logs.filter(notification_type='inactivity_alert')
        if last:
            qs = qs.filter(sent_at__date__gt=last)
        return not qs.exists()

    def __str__(self):
        return self.name


class AttendanceLog(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='attendance_logs',
    )
    check_in_date = models.DateField()
    check_in_time = models.TimeField()
    session_end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time when this session expires (default: 2 hours after check-in)",
    )

    class Meta:
        ordering = ['-check_in_date', '-check_in_time']

    def __str__(self):
        return f"{self.member.name} — {self.check_in_date} {self.check_in_time}"

    def compute_session_end_time(self, duration_minutes=120):
        """Calculate session end time (default 2 hours after check-in)."""
        from datetime import datetime, timedelta
        check_in = datetime.combine(self.check_in_date, self.check_in_time)
        end = check_in + timedelta(minutes=duration_minutes)
        self.session_end_time = end.time()
        return self.session_end_time