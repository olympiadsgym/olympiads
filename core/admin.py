from django.contrib import admin
from .models import MembershipPlan, Announcement, NotificationLog

admin.site.register(MembershipPlan)
admin.site.register(Announcement)
admin.site.register(NotificationLog)
