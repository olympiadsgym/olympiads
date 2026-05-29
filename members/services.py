"""
Member service layer — all ORM queries go here (NFR-SC02).
Views import from this module, never directly from models.
"""
import datetime
import secrets
import string

from django.db import transaction
from django.utils import timezone

from .models import Member, AttendanceLog, User
from core.models import MembershipPlan, Announcement, NotificationLog


# ── Member queries ─────────────────────────────────────────────────────────────

def get_active_members(query=None, status=None):
    qs = Member.objects.filter(is_active=True).select_related('plan')
    if query:
        qs = qs.filter(name__icontains=query)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('name')


def get_member_by_pk(pk):
    return Member.objects.select_related('plan', 'user').get(pk=pk, is_active=True)


def register_member(name, email, contact, plan_id, start_date):
    plan = MembershipPlan.objects.get(pk=plan_id)
    expiry_date = start_date + datetime.timedelta(days=plan.duration_days)
    alphabet = string.ascii_letters + string.digits
    temp_pw = ''.join(secrets.choice(alphabet) for _ in range(12))

    with transaction.atomic():
        user = User(email=email, role='member')
        user.set_password(temp_pw)
        user.save()
        member = Member.objects.create(
            name=name,
            email=email,
            contact=contact,
            plan=plan,
            start_date=start_date,
            expiry_date=expiry_date,
            status='Active',
            user=user,
        )
    return member, temp_pw


def deactivate_member(pk):
    member = Member.objects.get(pk=pk)
    member.is_active = False
    member.save(update_fields=['is_active'])
    return member


# ── Attendance queries ─────────────────────────────────────────────────────────

def get_recent_checkin(member, minutes=30):
    now = timezone.localtime()
    recent = (
        AttendanceLog.objects
        .filter(member=member)
        .order_by('-check_in_date', '-check_in_time')
        .first()
    )
    if not recent:
        return None
    last_dt = timezone.make_aware(
        datetime.datetime.combine(recent.check_in_date, recent.check_in_time)
    )
    return recent if (now - last_dt).total_seconds() < (minutes * 60) else None


def record_checkin(member):
    now = timezone.localtime()
    log = AttendanceLog.objects.create(
        member=member,
        check_in_date=now.date(),
        check_in_time=now.time(),
    )
    log.compute_session_end_time()
    log.save(update_fields=['session_end_time'])
    member.status = member.compute_status()
    member.save(update_fields=['status'])
    return log


# ── Announcements ──────────────────────────────────────────────────────────────

def get_all_announcements():
    return Announcement.objects.all()


# ── Notification log ───────────────────────────────────────────────────────────

def get_notification_logs(status=None):
    qs = NotificationLog.objects.select_related('member').order_by('-sent_at')
    if status:
        qs = qs.filter(status=status)
    return qs