from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/portal/login/', permanent=False)),
    path('gym-mgmt-2026/', include('core.urls')),
    path('gym-mgmt-2026/', include(('members.urls', 'members_admin'), namespace='members_admin')),
    path('portal/', include(('members.urls', 'members'), namespace='members')),
]