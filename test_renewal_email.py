import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olympiads.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from members.models import Member

pk = int(sys.argv[1]) if len(sys.argv) > 1 else None

if pk is None:
    print("\nUsage: python test_renewal_email.py <member_pk>")
    print("\nAvailable members:")
    for m in Member.objects.all():
        print(f"  pk={m.pk}  {m.name}  <{m.email}>")
    sys.exit(1)

member = Member.objects.select_related('plan').get(pk=pk)
print(f"\nSending renewal email to: {member.name} <{member.email}>")
print(f"From: {settings.DEFAULT_FROM_EMAIL}")
print(f"Plan: {member.plan.plan_name}")
print(f"Expiry: {member.expiry_date}\n")

html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="background:#F1F5F9; margin:0; padding:0; font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F1F5F9; padding:40px 16px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;">

        <tr>
          <td style="background:#0F172A; border-radius:14px 14px 0 0; padding:28px 36px 24px; text-align:center;">
            <span style="font-size:22px; font-weight:800; color:#FFFFFF; letter-spacing:2px;">OLYMPIADS</span><br>
            <span style="font-size:11px; color:#94A3B8; letter-spacing:3px; text-transform:uppercase;">Fitness &amp; Wellness</span>
          </td>
        </tr>

        <tr>
          <td style="background:#FFFFFF; padding:36px; border-left:1px solid #E2E8F0; border-right:1px solid #E2E8F0;">

            <p style="text-align:center; margin:0 0 20px 0;">
              <span style="background:#DCFCE7; color:#166534; font-size:12px; font-weight:600; padding:6px 16px; border-radius:999px; border:1px solid #BBF7D0;">
                Membership Renewed
              </span>
            </p>

            <h1 style="font-size:22px; font-weight:700; color:#0F172A; text-align:center; margin:0 0 8px 0;">
              You are all set, {member.name}!
            </h1>
            <p style="font-size:14px; color:#64748B; text-align:center; margin:0 0 28px 0; line-height:1.6;">
              Your OLYMPIADS membership has been successfully renewed. Keep up the great work!
            </p>

            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; margin-bottom:24px;">
              <tr>
                <td style="background:#0F172A; padding:10px 20px; border-radius:10px 10px 0 0;">
                  <span style="font-size:12px; font-weight:600; color:#F59E0B; text-transform:uppercase; letter-spacing:1px;">Renewed Membership Details</span>
                </td>
              </tr>
              <tr>
                <td width="50%" style="padding:14px 20px; border-bottom:1px solid #E2E8F0;">
                  <span style="font-size:11px; color:#94A3B8; display:block; margin-bottom:3px;">PLAN</span>
                  <span style="font-size:14px; font-weight:600; color:#0F172A;">{member.plan.plan_name}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:14px 20px; border-bottom:1px solid #E2E8F0;">
                  <span style="font-size:11px; color:#94A3B8; display:block; margin-bottom:3px;">START DATE</span>
                  <span style="font-size:14px; font-weight:500; color:#1E293B;">{member.start_date}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:14px 20px;">
                  <span style="font-size:11px; color:#94A3B8; display:block; margin-bottom:3px;">NEW EXPIRY DATE</span>
                  <span style="font-size:14px; font-weight:600; color:#22C55E;">{member.expiry_date}</span>
                </td>
              </tr>
            </table>

            <p style="font-size:13px; color:#94A3B8; text-align:center; margin:0;">
              Thank you for being part of the OLYMPIADS family. See you at the gym!
            </p>

          </td>
        </tr>

        <tr>
          <td style="background:#F8FAFC; border:1px solid #E2E8F0; border-top:none; border-radius:0 0 14px 14px; padding:20px 36px; text-align:center;">
            <p style="font-size:12px; color:#94A3B8; margin:0;">
              This is an automated message from OLYMPIADS Gym Management System. Do not reply.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

plain = (
    f"Hi {member.name},\n\n"
    f"Your OLYMPIADS membership has been successfully renewed.\n\n"
    f"Plan: {member.plan.plan_name}\n"
    f"Start Date: {member.start_date}\n"
    f"New Expiry Date: {member.expiry_date}\n\n"
    f"Thank you for being part of the OLYMPIADS family!\n\n"
    f"--- OLYMPIADS Gym Team"
)

try:
    msg = EmailMultiAlternatives(
        subject="[OLYMPIADS] Membership Successfully Renewed",
        body=plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[member.email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)
    print(f"SUCCESS - Email sent to {member.email}")
    print(f"Check the inbox and spam folder of {member.email}")
except Exception as e:
    print(f"FAILED - {type(e).__name__}: {e}")