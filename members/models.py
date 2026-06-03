import datetime
import secrets
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from .encryption import EncryptedFieldDescriptor, make_lookup_hash


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


class PasswordResetToken(models.Model):
    """Store password reset tokens with expiration."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reset_token')
    token = models.CharField(max_length=128, unique=True)  # BUG FIX: was 64 — token_urlsafe(48) produces exactly 64 chars leaving no margin; 128 is safe
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        """Check if token is still valid."""
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.email}"


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

    # Email is stored encrypted in _email, accessed via EncryptedFieldDescriptor
    _email = models.TextField(db_column='email_enc', unique=False)
    email_hash = models.CharField(max_length=64, unique=True, blank=True, default='')
    email = EncryptedFieldDescriptor('_email')

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

    def save(self, *args, **kwargs):
        """
        Override save to compute email_hash from the (possibly encrypted) email.
        The descriptor handles encryption/decryption automatically.
        """
        from .encryption import decrypt, make_lookup_hash
        
        # Extract plaintext email for hashing
        try:
            plaintext_email = decrypt(self._email) if self._email else ''
        except Exception:
            # If decryption fails (e.g., key missing, or _email is plaintext),
            # use the raw value so we never crash on save.
            plaintext_email = self._email or ''
        
        # Compute the lookup hash for this email
        self.email_hash = make_lookup_hash(plaintext_email)
        super().save(*args, **kwargs)

    def compute_status(self):
        """Compute the current membership status based on dates and check-ins."""
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
        """Return the number of days remaining in the membership."""
        today = timezone.localdate()
        return max(0, (self.expiry_date - today).days)

    def last_checkin(self):
        """Return the date of the member's last check-in, or None."""
        log = self.attendance_logs.order_by('-check_in_date', '-check_in_time').first()
        return log.check_in_date if log else None

    def is_newly_inactive(self):
        """Check if member has recently become inactive (no inactivity alert sent yet)."""
        if self.status != 'Inactive':
            return False
        last = self.last_checkin()
        qs = self.notification_logs.filter(notification_type='inactivity_alert')
        if last:
            qs = qs.filter(sent_at__date__gt=last)
        return not qs.exists()

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['email_hash']),
            models.Index(fields=['is_active']),
            models.Index(fields=['status']),
        ]

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
        indexes = [
            models.Index(fields=['member', '-check_in_date']),
        ]

    def __str__(self):
        return f"{self.member.name} — {self.check_in_date} {self.check_in_time}"

    def compute_session_end_time(self, duration_minutes=120):
        """Compute session end time based on check-in time and duration."""
        from datetime import datetime, timedelta
        check_in = datetime.combine(self.check_in_date, self.check_in_time)
        end = check_in + timedelta(minutes=duration_minutes)
        self.session_end_time = end.time()
        return self.session_end_time