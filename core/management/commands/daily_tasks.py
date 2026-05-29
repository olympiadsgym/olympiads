"""
Daily management command — run once per day via PythonAnywhere scheduler.
  python manage.py daily_tasks

Tasks:
  1. Recompute and persist member statuses.
  2. Send inactivity alerts for newly-inactive members.
  3. Send expiry notifications for members expiring within 7 days (if not already sent this cycle).
"""

import logging
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from members.models import Member
from core.models import NotificationLog

logger = logging.getLogger(__name__)


INACTIVITY_SUBJECT = "[OLYMPIADS] Member Inactivity Alert"
EXPIRY_SUBJECT = "[OLYMPIADS] Membership Expiring Soon"


def build_inactivity_body(member):
    return (
        f"Hi,\n\n"
        f"This is an automated alert from OLYMPIADS.\n\n"
        f"Member: {member.name}\n"
        f"Email: {member.email}\n"
        f"Plan: {member.plan}\n"
        f"Expiry Date: {member.expiry_date}\n"
        f"Last Check-In: {member.last_checkin() or 'No visits recorded'}\n\n"
        f"This member has been marked Inactive due to no recent gym visits.\n\n"
        f"— OLYMPIADS Automated System"
    )


def build_expiry_body(member):
    return (
        f"Hi {member.name},\n\n"
        f"This is a reminder from OLYMPIADS Gym.\n\n"
        f"Your {member.plan.plan_name} membership is expiring on {member.expiry_date}.\n"
        f"You have {member.days_remaining()} day(s) remaining.\n\n"
        f"Please visit the gym or contact staff to renew your membership.\n\n"
        f"— OLYMPIADS Gym Team"
    )


class Command(BaseCommand):
    help = 'Daily task: update statuses, send inactivity alerts and expiry notifications.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        self.stdout.write(f"[daily_tasks] Running for {today}")

        members_evaluated = 0
        inactivity_sent = 0
        expiry_sent = 0
        failures = 0
        task_errors = []  # collect per-member errors

        try:
            active_members = Member.objects.filter(is_active=True).select_related('plan')

            for member in active_members:
                members_evaluated += 1
                try:
                    # 1. Recompute and persist status
                    new_status = member.compute_status()
                    if member.status != new_status:
                        member.status = new_status
                        member.save(update_fields=['status'])

                    # 2. Inactivity alert
                    if member.is_newly_inactive():
                        log = NotificationLog.objects.create(
                            member=member,
                            notification_type='inactivity_alert',
                            status='sent',
                        )
                        try:
                            send_mail(
                                subject=INACTIVITY_SUBJECT,
                                message=build_inactivity_body(member),
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[settings.ADMIN_ALERT_EMAIL],
                                fail_silently=False,
                            )
                            log.mark_sent()
                            inactivity_sent += 1
                            self.stdout.write(f"  [inactivity] Sent alert for {member.name}")
                        except Exception as e:
                            logger.warning(f"Inactivity alert failed for {member.name}: {e}. Retrying...")
                            try:
                                send_mail(
                                    subject=INACTIVITY_SUBJECT,
                                    message=build_inactivity_body(member),
                                    from_email=settings.DEFAULT_FROM_EMAIL,
                                    recipient_list=[settings.ADMIN_ALERT_EMAIL],
                                    fail_silently=False,
                                )
                                log.mark_sent()
                                inactivity_sent += 1
                            except Exception as e2:
                                logger.error(f"Inactivity alert retry failed for {member.name}: {e2}")
                                log.mark_failed()
                                failures += 1

                    # 3. Expiry notification (status == Expiring Soon, not yet notified this cycle)
                    if member.status == 'Expiring Soon':
                        already_notified = NotificationLog.objects.filter(
                            member=member,
                            notification_type='expiry_notification',
                            status='sent',
                            sent_at__date__gte=member.expiry_date - timezone.timedelta(days=7),
                        ).exists()

                        if not already_notified:
                            log = NotificationLog.objects.create(
                                member=member,
                                notification_type='expiry_notification',
                                status='sent',
                            )
                            try:
                                send_mail(
                                    subject=EXPIRY_SUBJECT,
                                    message=build_expiry_body(member),
                                    from_email=settings.DEFAULT_FROM_EMAIL,
                                    recipient_list=[member.email],
                                    fail_silently=False,
                                )
                                log.mark_sent()
                                expiry_sent += 1
                                self.stdout.write(f"  [expiry] Sent notification to {member.email}")
                            except Exception as e:
                                logger.warning(f"Expiry notification failed for {member.name}: {e}. Retrying...")
                                try:
                                    send_mail(
                                        subject=EXPIRY_SUBJECT,
                                        message=build_expiry_body(member),
                                        from_email=settings.DEFAULT_FROM_EMAIL,
                                        recipient_list=[member.email],
                                        fail_silently=False,
                                    )
                                    log.mark_sent()
                                    expiry_sent += 1
                                except Exception as e2:
                                    logger.error(f"Expiry notification retry failed for {member.name}: {e2}")
                                    log.mark_failed()
                                    failures += 1

                except Exception as member_exc:
                    task_errors.append(f"  Member {member.pk} ({member.name}): {member_exc}")
                    logger.error(
                        f"Unexpected error processing member {member.pk}: {member_exc}",
                        exc_info=True,
                    )
                    failures += 1

        except Exception as fatal_exc:
            logger.critical(f"[daily_tasks] FATAL — task aborted: {fatal_exc}", exc_info=True)
            self.stderr.write(f"[daily_tasks] FATAL error: {fatal_exc}")
            raise  # re-raise so PythonAnywhere logs it as a failed task

        self.stdout.write(
            f"[daily_tasks] Complete — evaluated: {members_evaluated}, "
            f"inactivity alerts: {inactivity_sent}, expiry notifications: {expiry_sent}, "
            f"failures: {failures}"
        )
        if task_errors:
            self.stderr.write("Per-member errors:\n" + "\n".join(task_errors))