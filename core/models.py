from django.db import models


class MembershipPlan(models.Model):
    plan_name = models.CharField(max_length=50, unique=True)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.plan_name} ({self.duration_days} days)"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'members.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class NotificationLog(models.Model):
    NOTIFICATION_TYPES = [
        ('inactivity_alert', 'Inactivity Alert'),
        ('expiry_notification', 'Expiry Notification'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('retry_failed', 'Retry Failed'),
    ]

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='notification_logs',
    )
    notification_type = models.CharField(max_length=25, choices=NOTIFICATION_TYPES)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    retry_count = models.PositiveIntegerField(default=0)

    def mark_sent(self):
        self.status = 'sent'
        self.save()

    def mark_failed(self):
        self.retry_count += 1
        self.status = 'retry_failed' if self.retry_count >= 1 else 'failed'
        self.save()

    def __str__(self):
        return f"{self.notification_type} → {self.member} [{self.status}]"