from django.urls import path
from . import views

app_name = 'core'  # BUG FIX: was 'members' — caused all core: URL reversals to fail

urlpatterns = [
    # Admin login/logout
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Admin dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/refresh-statuses/', views.refresh_all_statuses, name='refresh_all_statuses'),
    # Check-in
    path('checkin/', views.checkin_view, name='checkin'),
    path('checkin/timeout/<int:log_id>/', views.timeout_member, name='timeout_member'),
    # Announcements
    path('announcements/', views.announcement_list, name='announcements'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    # Notifications log
    path('notifications/', views.notification_log_view, name='notification_log'),
    # Cron webhook
    path('cron/daily-tasks/', views.cron_daily_tasks, name='cron_daily_tasks'),
]