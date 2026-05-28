from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/refresh-statuses/', views.refresh_all_statuses, name='refresh_all_statuses'),
    path('checkin/', views.checkin_view, name='checkin'),
    path('attendance/<int:log_id>/timeout/', views.timeout_member, name='timeout_member'),
    path('announcements/', views.announcement_list, name='announcements'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    path('notifications/', views.notification_log_view, name='notification_log'),
]