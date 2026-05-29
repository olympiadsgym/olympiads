from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def admin_required(view_func):
    """Allow only authenticated admin-role sessions. Returns 403 for member sessions."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            # If they're a member trying to hit admin routes → 403
            if request.session.get('member_user_id'):
                return HttpResponseForbidden(
                    "<h1>403 Forbidden</h1><p>You do not have permission to access this page.</p>"
                )
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def member_required(view_func):
    """Allow only authenticated member-role sessions. Returns 403 for admin sessions."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('member_user_id'):
            if request.session.get('admin_id'):
                return HttpResponseForbidden(
                    "<h1>403 Forbidden</h1><p>You do not have permission to access this page.</p>"
                )
            return redirect('members:portal_login')
        return view_func(request, *args, **kwargs)
    return wrapper