from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse


class MidnightSessionExpireMiddleware:
    """
    Auto-logout users at midnight (12:00 AM).
    Checks if the session's start date has changed and clears the session if so.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user has an active session
        if request.session.get('admin_id') or request.session.get('member_user_id'):
            today = timezone.localdate()
            session_date = request.session.get('session_start_date')
            
            # If no session start date, set it
            if not session_date:
                request.session['session_start_date'] = str(today)
            else:
                # If date has changed (new day), logout the user
                if str(today) != session_date:
                    request.session.flush()
                    # Redirect to appropriate login page
                    if 'admin_id' in request.session:
                        return redirect('core:login')
                    elif 'member_user_id' in request.session:
                        return redirect('members:portal_login')
        
        response = self.get_response(request)
        return response
