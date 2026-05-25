from django.urls import path
from . import views


urlpatterns = [
    # Admin-facing member management (under gym-mgmt-2026/)
    path('members/', views.member_list_view, name='member_list'),
    path('members/register/', views.register_member, name='register'),
    path('members/<int:pk>/edit/', views.edit_member, name='edit_member'),
    path('members/<int:pk>/deactivate/', views.deactivate_member, name='deactivate_member'),
    # Member portal (under /portal/)
    path('login/', views.portal_login, name='portal_login'),
    path('logout/', views.portal_logout, name='portal_logout'),
    path('dashboard/', views.portal_dashboard, name='portal_dashboard'),
]
