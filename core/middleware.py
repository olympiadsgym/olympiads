import time
from django.utils import timezone
from django.shortcuts import redirect

SESSION_TIMEOUT_SECONDS = 30 * 60  # 30 minutes per NFR-S03


class SessionExpireMiddleware:
    """
    Enforces two expiry rules:
      1. Midnight expiry — session date changes → logout (existing behaviour).
      2. 30-minute inactivity — no request for 30 min → logout + message (NFR-S03/S04).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_admin = bool(request.session.get('admin_id'))
        is_member = bool(request.session.get('member_user_id'))

        if is_admin or is_member:
            today = timezone.localdate()
            now_ts = time.time()

            # Rule 1: midnight expiry
            session_date = request.session.get('session_start_date')
            if session_date and str(today) != session_date:
                request.session.flush()
                return redirect('core:login' if is_admin else 'members:portal_login')

            # Rule 2: 30-minute inactivity
            last_activity = request.session.get('last_activity')
            if last_activity and (now_ts - last_activity) > SESSION_TIMEOUT_SECONDS:
                request.session.flush()
                request.session['session_timed_out'] = True  # flag for message
                return redirect('core:login' if is_admin else 'members:portal_login')

            # Update last activity timestamp on every request
            request.session['last_activity'] = now_ts
            if not session_date:
                request.session['session_start_date'] = str(today)

        response = self.get_response(request)
        return response