import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.conf import settings
import datetime
import json

from .models import Announcement, NotificationLog
from .decorators import admin_required
from members.models import Member, AttendanceLog, User


def login_view(request):
    if request.session.get('admin_id'):
        return redirect('core:dashboard')
    # Clear the timeout flag once the login page renders so it shows only once
    timed_out = request.session.pop('session_timed_out', False)
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        try:
            user = User.objects.get(email=email, role='admin')
        except User.DoesNotExist:
            error = 'Invalid email or password.'
        else:
            if user.is_locked():
                error = 'Account locked for 15 minutes due to too many failed attempts.'
            elif user.check_password(password):
                user.reset_failed()
                request.session['admin_id'] = user.pk
                request.session['admin_email'] = user.email
                request.session['session_start_date'] = str(timezone.localdate())
                request.session['last_activity'] = time.time()
                return redirect('core:dashboard')
            else:
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
                user.increment_failed(ip_address=ip.split(',')[0].strip())
                error = 'Invalid email or password.'
    return render(request, 'core/login.html', {'error': error})


def logout_view(request):
    request.session.flush()
    return redirect('core:login')


@admin_required
def dashboard_view(request):
    today = timezone.localdate()
    active_members = Member.objects.filter(is_active=True)
    counts = {
        'active': active_members.filter(status='Active').count(),
        'inactive': active_members.filter(status='Inactive').count(),
        'expiring_soon': active_members.filter(status='Expiring Soon').count(),
        'expired': active_members.filter(status='Expired').count(),
        'total': active_members.count(),
    }
    expiring_soon = active_members.filter(status='Expiring Soon').order_by('expiry_date')[:10]
    todays_checkins = (
        AttendanceLog.objects
        .filter(check_in_date=today)
        .select_related('member')
        .order_by('-check_in_time')
    )
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    start_of_last_week = start_of_this_week - datetime.timedelta(days=7)
    end_of_last_week   = start_of_this_week - datetime.timedelta(days=1)
    this_week_count = AttendanceLog.objects.filter(
        check_in_date__gte=start_of_this_week,
        check_in_date__lte=today,
    ).count()
    last_week_count = AttendanceLog.objects.filter(
        check_in_date__gte=start_of_last_week,
        check_in_date__lte=end_of_last_week,
    ).count()
    if last_week_count > 0:
        week_change_pct = round((this_week_count - last_week_count) / last_week_count * 100)
    else:
        week_change_pct = None
    weekly_chart_labels = []
    weekly_chart_data = []
    for i in range(7, -1, -1):
        ws = start_of_this_week - datetime.timedelta(weeks=i)
        we = ws + datetime.timedelta(days=6)
        count = AttendanceLog.objects.filter(
            check_in_date__gte=ws,
            check_in_date__lte=min(we, today),
        ).count()
        weekly_chart_labels.append(ws.strftime('%b %d'))
        weekly_chart_data.append(count)
    return render(request, 'core/dashboard.html', {
        'counts': counts,
        'expiring_soon': expiring_soon,
        'todays_checkins': todays_checkins,
        'today': today,
        'this_week_count': this_week_count,
        'last_week_count': last_week_count,
        'week_change_pct': week_change_pct,
        'start_of_this_week': start_of_this_week,
        'weekly_chart_labels': json.dumps(weekly_chart_labels),
        'weekly_chart_data': json.dumps(weekly_chart_data),
    })


@admin_required
def refresh_all_statuses(request):
    if request.method == 'POST':
        members = Member.objects.filter(is_active=True)
        updated = 0
        for m in members:
            new_status = m.compute_status()
            if m.status != new_status:
                m.status = new_status
                m.save(update_fields=['status'])
                updated += 1
        messages.success(request, f"Statuses refreshed — {updated} member(s) updated.")
    return redirect('core:dashboard')


@admin_required
def checkin_view(request):
    checkin_result = None
    error = None
    query = request.GET.get('q', '').strip()

    # Always load all active members; filter by name if query provided
    all_members = Member.objects.filter(
        is_active=True
    ).select_related('plan').order_by('name')

    if query:
        search_results = all_members.filter(name__icontains=query)
    else:
        search_results = all_members
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        member = get_object_or_404(Member, pk=member_id, is_active=True)
        if member.status == 'Expired':
            error = f"Membership expired on {member.expiry_date}. Check-in not allowed."
        else:
            now = timezone.localtime()
            recent = AttendanceLog.objects.filter(
                member=member
            ).order_by('-check_in_date', '-check_in_time').first()
            if recent:
                last_dt = timezone.make_aware(
                    datetime.datetime.combine(recent.check_in_date, recent.check_in_time)
                )
                if (now - last_dt).total_seconds() < 1800:
                    error = (
                        f"Already checked in at {recent.check_in_time.strftime('%I:%M %p')} "
                        f"— less than 30 minutes ago."
                    )
            if not error:
                log = AttendanceLog.objects.create(
                    member=member,
                    check_in_date=now.date(),
                    check_in_time=now.time(),
                )
                log.compute_session_end_time(duration_minutes=120)
                log.save(update_fields=['session_end_time'])
                member.status = member.compute_status()
                member.save(update_fields=['status'])
                checkin_result = {'member': member, 'log': log}
    return render(request, 'core/checkin.html', {
        'search_results': search_results,
        'query': query,
        'checkin_result': checkin_result,
        'error': error,
    })


@admin_required
def timeout_member(request, log_id):
    log = get_object_or_404(AttendanceLog, pk=log_id)
    now = timezone.localtime()
    log.session_end_time = now.time()
    log.save(update_fields=['session_end_time'])
    messages.success(request, f"Session ended for {log.member.name}.")
    return redirect('core:dashboard')


@admin_required
def announcement_list(request):
    announcements = Announcement.objects.all()
    return render(request, 'core/announcements.html', {'announcements': announcements})


@admin_required
def announcement_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        if title and body:
            admin_user = User.objects.get(pk=request.session['admin_id'])
            Announcement.objects.create(title=title, body=body, created_by=admin_user)
            messages.success(request, 'Announcement posted.')
        else:
            messages.error(request, 'Title and body are required.')
    return redirect('core:announcements')


@admin_required
def announcement_delete(request, pk):
    if request.method == 'POST':
        announcement = get_object_or_404(Announcement, pk=pk)
        announcement.delete()
        messages.success(request, 'Announcement deleted.')
    return redirect('core:announcements')


@admin_required
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        if title and body:
            announcement.title = title
            announcement.body = body
            announcement.save()
            messages.success(request, 'Announcement updated.')
            return redirect('core:announcements')
        else:
            messages.error(request, 'Title and body are required.')
    return render(request, 'core/announcement_edit.html', {'announcement': announcement})


import hmac
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse


@csrf_exempt
@require_POST
def cron_daily_tasks(request):
    """
    Webhook called by Vercel Cron to run the daily_tasks management command.

    Vercel automatically sets Authorization: Bearer <CRON_SECRET> on every
    cron-triggered request.  We verify it with a constant-time comparison so
    the endpoint cannot be triggered by anyone who does not know the secret.
    """
    secret = settings.CRON_SECRET
    if not secret:
        return JsonResponse({'error': 'CRON_SECRET is not configured on this server.'}, status=500)

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    expected = f'Bearer {secret}'

    if not hmac.compare_digest(auth_header, expected):
        return JsonResponse({'error': 'Unauthorized.'}, status=401)

    try:
        from django.core.management import call_command
        import logging as _logging
        configured_hour = settings.DAILY_TASK_HOUR
        configured_minute = settings.DAILY_TASK_MINUTE
        _logging.getLogger(__name__).info(
            'cron_daily_tasks triggered. Configured schedule: %02d:%02d UTC '
            '(DAILY_TASK_HOUR=%s, DAILY_TASK_MINUTE=%s). '
            'Verify this matches the schedule in vercel.json.',
            configured_hour, configured_minute, configured_hour, configured_minute,
        )
        call_command('daily_tasks')
        return JsonResponse({
            'status': 'ok',
            'configured_schedule_utc': f'{configured_hour:02d}:{configured_minute:02d}',
        })
    except Exception as exc:
        import logging as _logging2
        _logging2.getLogger(__name__).exception('cron_daily_tasks failed')
        return JsonResponse({'error': str(exc)}, status=500)


@admin_required
def notification_log_view(request):
    status_filter = request.GET.get('status', '')
    logs = NotificationLog.objects.select_related('member').order_by('-sent_at')
    if status_filter:
        logs = logs.filter(status=status_filter)
    paginator = Paginator(logs, 30)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/notification_log.html', {
        'page_obj': page,
        'status_filter': status_filter,
        'status_choices': NotificationLog.STATUS_CHOICES,
    })