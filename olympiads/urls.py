from django.contrib.staticfiles.views import serve as serve_static
from django.urls import path, include, re_path

urlpatterns = [
    path('gym-mgmt-2026/', include('core.urls')),
    path('gym-mgmt-2026/', include('members.urls')),
    path('portal/', include(('members.urls', 'members'), namespace='members')),
    re_path(r'^static/(?P<path>.*)$', serve_static, {'insecure': True}),
]
