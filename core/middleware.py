from django.utils import timezone
from django.shortcuts import redirect


class MidnightSessionExpireMiddleware:
    """
    Auto-logout users at midnight (12:00 AM).
    Checks if the session's start date has changed and clears the session if so.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_admin = bool(request.session.get('admin_id'))
        is_member = bool(request.session.get('member_user_id'))

        if is_admin or is_member:
            today = timezone.localdate()
            session_date = request.session.get('session_start_date')

            if not session_date:
                request.session['session_start_date'] = str(today)
            elif str(today) != session_date:
                # Capture role BEFORE flushing the session
                request.session.flush()
                if is_admin:
                    return redirect('core:login')
                else:
                    return redirect('members:portal_login')

        response = self.get_response(request)
        return response