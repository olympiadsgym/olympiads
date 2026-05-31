from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Admin/Staff Portal
    path('', include('core.urls')),
    # Member Portal
    path('members/', include('members.urls')),
]