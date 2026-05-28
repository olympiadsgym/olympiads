import csv
import logging
import secrets
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse

logger = logging.getLogger(__name__)

from core.models import MembershipPlan, Announcement
from core.decorators import admin_required, member_required
from .models import Member, AttendanceLog, User

PORTAL_LOGIN_URL = "https://olympiads-beta.vercel.app/portal/login/"


def _generate_temp_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# --- Admin: Member Management ------------------------------------

@admin_required
def member_list_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    members = Member.objects.filter(is_active=True).select_related('plan')

    if query:
        members = members.filter(name__icontains=query)
    if status_filter:
        members = members.filter(status=status_filter)

    members = members.order_by('name')
    paginator = Paginator(members, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'members/member_list.html', {
        'page_obj': page,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Member.STATUS_CHOICES,
    })


@admin_required
def export_members_csv(request):
    """Export the current member list as a CSV file."""
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    members = Member.objects.filter(is_active=True).select_related('plan')
    if query:
        members = members.filter(name__icontains=query)
    if status_filter:
        members = members.filter(status=status_filter)
    members = members.order_by('name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="olympiads_members.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Contact', 'Plan', 'Status', 'Start Date', 'Expiry Date', 'Days Remaining'])
    for m in members:
        writer.writerow([
            m.name,
            m.email,
            m.contact,
            m.plan.plan_name,
            m.status,
            m.start_date,
            m.expiry_date,
            m.days_remaining,
        ])

    return response


@admin_required
def register_member(request):
    plans = MembershipPlan.objects.all().order_by('price')
    error = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        contact = request.POST.get('contact', '').strip()
        plan_id = request.POST.get('plan_id')
        start_date_str = request.POST.get('start_date')

        if not all([name, email, contact, plan_id, start_date_str]):
            error = 'All fields are required.'
        else:
            existing_member = Member.objects.filter(email=email).first()
            if existing_member and existing_member.is_active:
                error = 'This email is already registered to an active member.'
            else:
                try:
                    plan = MembershipPlan.objects.get(pk=plan_id)
                    from datetime import date
                    start_date = date.fromisoformat(start_date_str)
                    expiry_date = start_date + timezone.timedelta(days=plan.duration_days)

                    temp_pw = _generate_temp_password()

                    if existing_member:
                        # Re-activating a previously deactivated member
                        member = existing_member
                        member.name = name
                        member.contact = contact
                        member.plan = plan
                        member.start_date = start_date
                        member.expiry_date = expiry_date
                        member.status = 'Active'
                        member.is_active = True
                        member.save()

                        # Reset their portal password
                        if member.user:
                            member.user.set_password(temp_pw)
                            member.user.reset_failed()
                            member.user.save()
                        else:
                            user = User(email=email, role='member')
                            user.set_password(temp_pw)
                            user.save()
                            member.user = user
                            member.save(update_fields=['user'])
                    else:
                        # Brand new member
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

                    # Email credentials to member
                    try:
                        plain_text = (
                            f"Hi {name},\n\n"
                            f"Welcome to OLYMPIADS Gym! Your membership is now active.\n\n"
                            f"Portal Login: {PORTAL_LOGIN_URL}\n"
                            f"Email: {email}\n"
                            f"Password: {temp_pw}\n\n"
                            f"Plan: {plan.plan_name}\n"
                            f"Start Date: {start_date}\n"
                            f"Expiry Date: {expiry_date}\n\n"
                            f"Please change your password after your first login.\n\n"
                            f"— OLYMPIADS Gym"
                        )

                        html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#0f1117;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f1117;padding:40px 16px;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

          <!-- Header -->
          <tr>
            <td align="center" style="padding-bottom:28px;">
              <span style="font-size:22px;font-weight:800;letter-spacing:2px;color:#f5a623;">OLYMPIADS</span>
              <p style="margin:4px 0 0;font-size:12px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;">Gym Management</p>
            </td>
          </tr>

          <!-- Card -->
          <tr>
            <td style="background:#1a1d2e;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.07);">

              <!-- Gold top bar -->
              <div style="height:4px;background:linear-gradient(90deg,#f5a623,#f7c36a);"></div>

              <!-- Body -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding:36px 36px 28px;">

                    <!-- Greeting -->
                    <p style="margin:0 0 6px;font-size:13px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;">Welcome aboard</p>
                    <h1 style="margin:0 0 20px;font-size:26px;font-weight:700;color:#f9fafb;">Hi {name}! 👋</h1>
                    <p style="margin:0 0 28px;font-size:15px;color:#d1d5db;line-height:1.6;">
                      Your membership at <strong style="color:#f5a623;">OLYMPIADS Gym</strong> is now active. Here are your portal credentials — keep them safe!
                    </p>

                    <!-- Credentials box -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f1117;border-radius:10px;border:1px solid rgba(245,166,35,0.2);margin-bottom:28px;">
                      <tr>
                        <td style="padding:20px 24px;">
                          <p style="margin:0 0 4px;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:1px;">Email</p>
                          <p style="margin:0;font-size:14px;color:#f9fafb;">{email}</p>
                        </td>
                      </tr>
                      <tr>
                        <td style="border-top:1px solid rgba(255,255,255,0.05);padding:16px 24px;">
                          <p style="margin:0 0 4px;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:1px;">Temporary Password</p>
                          <p style="margin:0;font-size:16px;font-weight:700;color:#f5a623;letter-spacing:2px;font-family:monospace;">{temp_pw}</p>
                        </td>
                      </tr>
                    </table>

                    <!-- Login button -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
                      <tr>
                        <td align="center">
                          <a href="{PORTAL_LOGIN_URL}"
                             style="display:inline-block;padding:14px 40px;background:linear-gradient(90deg,#f5a623,#f7c36a);color:#0f1117;font-size:15px;font-weight:700;text-decoration:none;border-radius:8px;letter-spacing:0.5px;">
                            Login to Your Portal
                          </a>
                        </td>
                      </tr>
                      <tr>
                        <td align="center" style="padding-top:10px;">
                          <p style="margin:0;font-size:12px;color:#6b7280;">
                            Or copy this link: <a href="{PORTAL_LOGIN_URL}" style="color:#f5a623;text-decoration:none;">{PORTAL_LOGIN_URL}</a>
                          </p>
                        </td>
                      </tr>
                    </table>

                    <!-- Membership details -->
                    <p style="margin:0 0 14px;font-size:13px;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;">Membership Details</p>
                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
                      <tr>
                        <td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                          <span style="font-size:13px;color:#6b7280;">Plan</span>
                        </td>
                        <td align="right" style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                          <span style="font-size:13px;font-weight:600;color:#f9fafb;">{plan.plan_name}</span>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                          <span style="font-size:13px;color:#6b7280;">Start Date</span>
                        </td>
                        <td align="right" style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                          <span style="font-size:13px;font-weight:600;color:#f9fafb;">{start_date}</span>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:10px 0;">
                          <span style="font-size:13px;color:#6b7280;">Expiry Date</span>
                        </td>
                        <td align="right" style="padding:10px 0;">
                          <span style="font-size:13px;font-weight:600;color:#f9fafb;">{expiry_date}</span>
                        </td>
                      </tr>
                    </table>

                    <p style="margin:0;font-size:13px;color:#6b7280;line-height:1.6;">
                      Please change your password after your first login.
                    </p>

                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="padding:24px 0 0;">
              <p style="margin:0;font-size:12px;color:#4b5563;">© OLYMPIADS Gym · This is an automated message, please do not reply.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

                        msg = EmailMultiAlternatives(
                            subject="Welcome to OLYMPIADS Gym — Your Portal Login",
                            body=plain_text,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[email],
                        )
                        msg.attach_alternative(html_body, "text/html")
                        msg.send(fail_silently=False)

                    except Exception as e:
                        logger.exception("Failed to send registration email to %s", email)
                        messages.warning(
                            request,
                            "Member was registered, but the welcome email could not be sent. "
                            f"Email error: {e}"
                        )

                    messages.success(request, f"{name} registered successfully.")
                    return redirect('members:member_list')

                except MembershipPlan.DoesNotExist:
                    error = 'Invalid membership plan selected.'
                except ValueError:
                    error = 'Invalid date format.'

    return render(request, 'members/register.html', {
        'plans': plans,
        'error': error,
        'today': timezone.localdate().isoformat(),
    })


@admin_required
def edit_member(request, pk):
    member = get_object_or_404(Member, pk=pk, is_active=True)
    plans = MembershipPlan.objects.all().order_by('price')
    error = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        contact = request.POST.get('contact', '').strip()
        plan_id = request.POST.get('plan_id')
        start_date_str = request.POST.get('start_date')

        if not all([name, email, contact, plan_id, start_date_str]):
            error = 'All fields are required.'
        elif Member.objects.filter(email=email).exclude(pk=pk).exists():
            error = 'This email is already used by another member.'
        else:
            try:
                plan = MembershipPlan.objects.get(pk=plan_id)
                from datetime import date
                start_date = date.fromisoformat(start_date_str)
                expiry_date = start_date + timezone.timedelta(days=plan.duration_days)

                member.name = name
                member.contact = contact
                member.plan = plan
                member.start_date = start_date
                member.expiry_date = expiry_date
                member.status = member.compute_status()

                if member.email != email:
                    if member.user:
                        member.user.email = email
                        member.user.save(update_fields=['email'])
                    member.email = email

                member.save()
                messages.success(request, f"{member.name} updated.")
                return redirect('members:member_list')

            except MembershipPlan.DoesNotExist:
                error = 'Invalid membership plan.'
            except ValueError:
                error = 'Invalid date format.'

    return render(request, 'members/edit_member.html', {
        'member': member,
        'plans': plans,
        'error': error,
    })


@admin_required
def renew_member(request, pk):
    """Renew a member's plan from today, extending by the plan's duration."""
    if request.method == 'POST':
        member = get_object_or_404(Member, pk=pk, is_active=True)
        today = timezone.localdate()
        member.start_date = today
        member.expiry_date = today + timezone.timedelta(days=member.plan.duration_days)
        member.status = member.compute_status()
        member.save()
        messages.success(request, f"{member.name}'s membership renewed until {member.expiry_date}.")
    return redirect('members:edit_member', pk=pk)


@admin_required
def deactivate_member(request, pk):
    if request.method == 'POST':
        member = get_object_or_404(Member, pk=pk)
        member.is_active = False
        member.save(update_fields=['is_active'])
        messages.success(request, f"{member.name} has been deactivated.")
    return redirect('members:member_list')


# --- Member Portal ------------------------------------------------

def portal_login(request):
    if request.session.get('member_user_id'):
        return redirect('members:portal_dashboard')

    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            user = User.objects.get(email=email, role='member')
        except User.DoesNotExist:
            error = 'Invalid email or password.'
        else:
            if user.is_locked():
                error = 'Account locked for 15 minutes due to too many failed attempts.'
            elif user.check_password(password):
                user.reset_failed()
                request.session['member_user_id'] = user.pk
                request.session['session_start_date'] = str(timezone.localdate())
                return redirect('members:portal_dashboard')
            else:
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
                user.increment_failed(ip_address=ip.split(',')[0].strip())
                error = 'Invalid email or password.'

    return render(request, 'members/portal_login.html', {'error': error})


def portal_logout(request):
    request.session.flush()
    return redirect('members:portal_login')


@member_required
def portal_dashboard(request):
    user = get_object_or_404(User, pk=request.session['member_user_id'])
    member = get_object_or_404(Member, user=user, is_active=True)

    member.status = member.compute_status()
    member.save(update_fields=['status'])

    all_logs = member.attendance_logs.order_by('-check_in_date', '-check_in_time')
    paginator = Paginator(all_logs, 20)
    page = paginator.get_page(request.GET.get('page'))

    announcements = Announcement.objects.all()[:10]

    return render(request, 'members/portal_dashboard.html', {
        'member': member,
        'page_obj': page,
        'announcements': announcements,
    })


@member_required
def change_password(request):
    """Allow a portal member to change their own password."""
    user = get_object_or_404(User, pk=request.session['member_user_id'])
    error = None
    success = False

    if request.method == 'POST':
        current_pw = request.POST.get('current_password', '')
        new_pw = request.POST.get('new_password', '')
        confirm_pw = request.POST.get('confirm_password', '')

        if not user.check_password(current_pw):
            error = 'Current password is incorrect.'
        elif len(new_pw) < 8:
            error = 'New password must be at least 8 characters.'
        elif not any(c.isupper() for c in new_pw):
            error = 'New password must contain at least one uppercase letter.'
        elif not any(c.islower() for c in new_pw):
            error = 'New password must contain at least one lowercase letter.'
        elif not any(c.isdigit() for c in new_pw):
            error = 'New password must contain at least one number.'
        elif new_pw != confirm_pw:
            error = 'New passwords do not match.'
        else:
            user.set_password(new_pw)
            user.save()
            # Re-save session so it stays valid after password change
            request.session['member_user_id'] = user.pk
            request.session.modified = True
            success = True

    return render(request, 'members/change_password.html', {
        'error': error,
        'success': success,
    })