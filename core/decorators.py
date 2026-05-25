from functools import wraps
from django.shortcuts import redirect


def admin_required(view_func):
    """Allow only authenticated admin-role sessions."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def member_required(view_func):
    """Allow only authenticated member-role sessions."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('member_user_id'):
            return redirect('members:portal_login')
        return view_func(request, *args, **kwargs)
    return wrapper
