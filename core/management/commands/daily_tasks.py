import logging
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone

from members.models import Member
from core.models import NotificationLog

logger = logging.getLogger(__name__)


INACTIVITY_SUBJECT = "[OLYMPIADS] Member Inactivity Alert"
EXPIRY_SUBJECT = "[OLYMPIADS] Your Membership is Expiring Soon"


# ---------------------------------------------------------------------------
# Plain-text fallbacks
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# HTML email builders
# ---------------------------------------------------------------------------

def _email_wrapper(body_html: str) -> str:
    """Wraps content in the OLYMPIADS branded email shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OLYMPIADS</title>
  <!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: #F1F5F9;
      font-family: 'Poppins', Arial, sans-serif;
      color: #0F172A;
      -webkit-font-smoothing: antialiased;
    }}
    a {{ color: inherit; text-decoration: none; }}
  </style>
</head>
<body style="background:#F1F5F9; margin:0; padding:0;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F1F5F9; padding:40px 16px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;">

          <!-- HEADER -->
          <tr>
            <td style="background:#0F172A; border-radius:14px 14px 0 0; padding:28px 36px 24px; text-align:center;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center">
                    <!-- Logo mark -->
                    <div style="display:inline-block; background:#F59E0B; border-radius:10px; width:44px; height:44px; line-height:44px; text-align:center; font-size:22px; font-weight:800; color:#0F172A; margin-bottom:10px;">O</div>
                    <br>
                    <span style="font-family:'Poppins',Arial,sans-serif; font-size:22px; font-weight:800; color:#FFFFFF; letter-spacing:2px;">OLYMPIADS</span>
                    <br>
                    <span style="font-family:'Poppins',Arial,sans-serif; font-size:11px; font-weight:500; color:#94A3B8; letter-spacing:3px; text-transform:uppercase;">Fitness &amp; Wellness</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="background:#FFFFFF; padding:36px 36px 28px; border-left:1px solid #E2E8F0; border-right:1px solid #E2E8F0;">
              {body_html}
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background:#F8FAFC; border:1px solid #E2E8F0; border-top:none; border-radius:0 0 14px 14px; padding:20px 36px; text-align:center;">
              <p style="font-family:'Poppins',Arial,sans-serif; font-size:12px; color:#94A3B8; margin-bottom:4px;">
                This is an automated message from OLYMPIADS Gym Management System.
              </p>
              <p style="font-family:'Poppins',Arial,sans-serif; font-size:12px; color:#CBD5E1;">
                Please do not reply to this email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def build_inactivity_html(member):
    last_checkin = member.last_checkin()
    last_checkin_str = str(last_checkin) if last_checkin else "No visits recorded"

    body = f"""
      <!-- Alert badge -->
      <p style="text-align:center; margin-bottom:24px;">
        <span style="display:inline-block; background:#FEF9C3; color:#854D0E; font-family:'Poppins',Arial,sans-serif; font-size:12px; font-weight:600; padding:6px 16px; border-radius:999px; border:1px solid #FDE68A; letter-spacing:0.5px; text-transform:uppercase;">
          ⚠ Inactivity Alert
        </span>
      </p>

      <h1 style="font-family:'Poppins',Arial,sans-serif; font-size:22px; font-weight:700; color:#0F172A; text-align:center; margin-bottom:8px; line-height:1.3;">
        Member Marked Inactive
      </h1>
      <p style="font-family:'Poppins',Arial,sans-serif; font-size:14px; color:#64748B; text-align:center; margin-bottom:28px; line-height:1.6;">
        The following member has been automatically marked inactive due to no recent gym visits.
      </p>

      <!-- Member info card -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; margin-bottom:24px; overflow:hidden;">
        <tr>
          <td style="padding:0;">
            <!-- Card header strip -->
            <div style="background:#0F172A; padding:10px 20px; border-radius:10px 10px 0 0;">
              <span style="font-family:'Poppins',Arial,sans-serif; font-size:12px; font-weight:600; color:#F59E0B; text-transform:uppercase; letter-spacing:1px;">Member Details</span>
            </div>
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="padding:4px 0;">
              <tr>
                <td style="padding:12px 20px; border-bottom:1px solid #E2E8F0;">
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:12px; color:#94A3B8; display:block; margin-bottom:2px;">MEMBER NAME</span>
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:15px; font-weight:600; color:#0F172A;">{member.name}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 20px; border-bottom:1px solid #E2E8F0;">
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:12px; color:#94A3B8; display:block; margin-bottom:2px;">EMAIL ADDRESS</span>
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:14px; color:#1E293B;">{member.email}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 20px; border-bottom:1px solid #E2E8F0;">
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:12px; color:#94A3B8; display:block; margin-bottom:2px;">MEMBERSHIP PLAN</span>
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:14px; color:#1E293B;">{member.plan}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 20px; border-bottom:1px solid #E2E8F0;">
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:12px; color:#94A3B8; display:block; margin-bottom:2px;">EXPIRY DATE</span>
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:14px; color:#1E293B;">{member.expiry_date}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 20px;">
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:12px; color:#94A3B8; display:block; margin-bottom:2px;">LAST CHECK-IN</span>
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:14px; color:#1E293B;">{last_checkin_str}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <p style="font-family:'Poppins',Arial,sans-serif; font-size:13px; color:#64748B; text-align:center; line-height:1.6;">
        You may want to reach out to this member to encourage their return.
      </p>
    """
    return _email_wrapper(body)


def build_expiry_html(member):
    days = member.days_remaining()

    # Choose urgency color
    if days <= 2:
        badge_bg, badge_color, badge_border = "#FEE2E2", "#991B1B", "#FECACA"
        badge_label = "🔴 Expiring Very Soon"
        days_color = "#EF4444"
    elif days <= 4:
        badge_bg, badge_color, badge_border = "#FFEDD5", "#9A3412", "#FED7AA"
        badge_label = "🟠 Expiring Soon"
        days_color = "#F97316"
    else:
        badge_bg, badge_color, badge_border = "#FEF9C3", "#854D0E", "#FDE68A"
        badge_label = "⚠ Membership Reminder"
        days_color = "#F59E0B"

    body = f"""
      <!-- Badge -->
      <p style="text-align:center; margin-bottom:24px;">
        <span style="display:inline-block; background:{badge_bg}; color:{badge_color}; font-family:'Poppins',Arial,sans-serif; font-size:12px; font-weight:600; padding:6px 16px; border-radius:999px; border:1px solid {badge_border}; letter-spacing:0.5px; text-transform:uppercase;">
          {badge_label}
        </span>
      </p>

      <h1 style="font-family:'Poppins',Arial,sans-serif; font-size:22px; font-weight:700; color:#0F172A; text-align:center; margin-bottom:8px; line-height:1.3;">
        Hi {member.name}, your membership<br>is expiring soon!
      </h1>
      <p style="font-family:'Poppins',Arial,sans-serif; font-size:14px; color:#64748B; text-align:center; margin-bottom:28px; line-height:1.6;">
        Don't lose access to OLYMPIADS. Renew now to keep your streak going.
      </p>

      <!-- Days remaining pill -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:28px;">
        <tr>
          <td align="center">
            <div style="display:inline-block; background:#0F172A; border-radius:12px; padding:20px 40px; text-align:center;">
              <span style="font-family:'Poppins',Arial,sans-serif; font-size:48px; font-weight:800; color:{days_color}; display:block; line-height:1;">{days}</span>
              <span style="font-family:'Poppins',Arial,sans-serif; font-size:13px; font-weight:500; color:#94A3B8; letter-spacing:2px; text-transform:uppercase;">
                {'day' if days == 1 else 'days'} remaining
              </span>
            </div>
          </td>
        </tr>
      </table>

      <!-- Membership details card -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; margin-bottom:28px; overflow:hidden;">
        <tr>
          <td style="padding:0;">
            <div style="background:#0F172A; padding:10px 20px; border-radius:10px 10px 0 0;">
              <span style="font-family:'Poppins',Arial,sans-serif; font-size:12px; font-weight:600; color:#F59E0B; text-transform:uppercase; letter-spacing:1px;">Membership Details</span>
            </div>
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td width="50%" style="padding:14px 20px; border-bottom:1px solid #E2E8F0; border-right:1px solid #E2E8F0;">
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:11px; color:#94A3B8; display:block; margin-bottom:3px; text-transform:uppercase; letter-spacing:0.5px;">Plan</span>
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:14px; font-weight:600; color:#0F172A;">{member.plan.plan_name}</span>
                </td>
                <td width="50%" style="padding:14px 20px; border-bottom:1px solid #E2E8F0;">
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:11px; color:#94A3B8; display:block; margin-bottom:3px; text-transform:uppercase; letter-spacing:0.5px;">Status</span>
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:14px; font-weight:600; color:{days_color};">Expiring Soon</span>
                </td>
              </tr>
              <tr>
                <td width="50%" style="padding:14px 20px; border-right:1px solid #E2E8F0;">
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:11px; color:#94A3B8; display:block; margin-bottom:3px; text-transform:uppercase; letter-spacing:0.5px;">Start Date</span>
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:14px; font-weight:500; color:#1E293B;">{member.start_date}</span>
                </td>
                <td width="50%" style="padding:14px 20px;">
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:11px; color:#94A3B8; display:block; margin-bottom:3px; text-transform:uppercase; letter-spacing:0.5px;">Expiry Date</span>
                  <span style="font-family:'Poppins',Arial,sans-serif; font-size:14px; font-weight:600; color:{days_color};">{member.expiry_date}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- CTA -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:20px;">
        <tr>
          <td align="center">
            <div style="background:#F59E0B; border-radius:8px; padding:14px 32px; display:inline-block;">
              <span style="font-family:'Poppins',Arial,sans-serif; font-size:15px; font-weight:700; color:#0F172A; letter-spacing:0.3px;">
                Renew Your Membership
              </span>
            </div>
          </td>
        </tr>
      </table>

      <p style="font-family:'Poppins',Arial,sans-serif; font-size:13px; color:#94A3B8; text-align:center; line-height:1.6;">
        Visit the gym or contact our staff to renew. We'd love to keep you as part of the OLYMPIADS family!
      </p>
    """
    return _email_wrapper(body)


# ---------------------------------------------------------------------------
# Shared email sender
# ---------------------------------------------------------------------------

def send_html_mail(subject, text_body, html_body, from_email, recipient_list):
    """Send an email with both plain-text and HTML alternatives."""
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=recipient_list,
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


# ---------------------------------------------------------------------------
# Management command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = 'Daily task: update statuses, send inactivity alerts and expiry notifications.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        self.stdout.write(f"[daily_tasks] Running for {today}")

        members_evaluated = 0
        inactivity_sent = 0
        expiry_sent = 0
        failures = 0
        task_errors = []

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

                    # 2. Inactivity alert (sent to admin)
                    if member.is_newly_inactive():
                        log = NotificationLog.objects.create(
                            member=member,
                            notification_type='inactivity_alert',
                            status='sent',
                        )
                        try:
                            send_html_mail(
                                subject=INACTIVITY_SUBJECT,
                                text_body=build_inactivity_body(member),
                                html_body=build_inactivity_html(member),
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[settings.ADMIN_ALERT_EMAIL],
                            )
                            log.mark_sent()
                            inactivity_sent += 1
                            self.stdout.write(f"  [inactivity] Sent alert for {member.name}")
                        except Exception as e:
                            logger.warning(f"Inactivity alert failed for {member.name}: {e}. Retrying...")
                            try:
                                send_html_mail(
                                    subject=INACTIVITY_SUBJECT,
                                    text_body=build_inactivity_body(member),
                                    html_body=build_inactivity_html(member),
                                    from_email=settings.DEFAULT_FROM_EMAIL,
                                    recipient_list=[settings.ADMIN_ALERT_EMAIL],
                                )
                                log.mark_sent()
                                inactivity_sent += 1
                            except Exception as e2:
                                logger.error(f"Inactivity alert retry failed for {member.name}: {e2}")
                                log.mark_failed()
                                failures += 1

                    # 3. Expiry notification (sent to member)
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
                                send_html_mail(
                                    subject=EXPIRY_SUBJECT,
                                    text_body=build_expiry_body(member),
                                    html_body=build_expiry_html(member),
                                    from_email=settings.DEFAULT_FROM_EMAIL,
                                    recipient_list=[member.email],
                                )
                                log.mark_sent()
                                expiry_sent += 1
                                self.stdout.write(f"  [expiry] Sent notification to {member.email}")
                            except Exception as e:
                                logger.warning(f"Expiry notification failed for {member.name}: {e}. Retrying...")
                                try:
                                    send_html_mail(
                                        subject=EXPIRY_SUBJECT,
                                        text_body=build_expiry_body(member),
                                        html_body=build_expiry_html(member),
                                        from_email=settings.DEFAULT_FROM_EMAIL,
                                        recipient_list=[member.email],
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
            raise

        self.stdout.write(
            f"[daily_tasks] Complete — evaluated: {members_evaluated}, "
            f"inactivity alerts: {inactivity_sent}, expiry notifications: {expiry_sent}, "
            f"failures: {failures}"
        )
        if task_errors:
            self.stderr.write("Per-member errors:\n" + "\n".join(task_errors))