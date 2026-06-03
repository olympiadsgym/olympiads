from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import HttpResponse
import base64


def favicon_view(request):
    """Serve a minimal favicon to silence repeated 404 log warnings."""
    # 1x1 transparent ICO
    ico_b64 = (
        b'AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAA'
        b'QAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    )
    try:
        ico = base64.b64decode(ico_b64)
    except Exception:
        ico = b''
    return HttpResponse(ico, content_type='image/x-icon')


urlpatterns = [
    path('admin/', admin.site.urls),
    # Serve favicon to suppress repeated 404 warnings
    path('favicon.ico', favicon_view),
    # Admin/Staff Portal
    path('', include('core.urls')),
    # Convenience redirect: /login/ -> / (admin login lives at root)
    path('login/', RedirectView.as_view(url='/', permanent=False)),
    # Member Portal
    path('members/', include('members.urls')),
]