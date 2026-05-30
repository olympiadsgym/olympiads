from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Root → member portal login
    path('', RedirectView.as_view(url='/portal/login/', permanent=False)),

    # Easy admin shortcut
    path('admin-login/', RedirectView.as_view(url='/gym-mgmt-2026/', permanent=False)),

    # Admin area
    path('gym-mgmt-2026/', include('core.urls')),
    path('gym-mgmt-2026/', include(('members.urls', 'members_admin'), namespace='members_admin')),

    # Member portal
    path('portal/', include(('members.urls', 'members'), namespace='members')),
]