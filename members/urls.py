from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    # Admin-facing member management (included under /members/ in olympiads/urls.py)
    path('', views.member_list_view, name='member_list'),
    path('export/', views.export_members_csv, name='export_members_csv'),
    path('register/', views.register_member, name='register'),
    path('<int:pk>/edit/', views.edit_member, name='edit_member'),
    path('<int:pk>/renew/', views.renew_member, name='renew_member'),
    path('<int:pk>/deactivate/', views.deactivate_member, name='deactivate_member'),
    # Member portal
    path('login/', views.portal_login, name='portal_login'),
    path('logout/', views.portal_logout, name='portal_logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('dashboard/', views.portal_dashboard, name='portal_dashboard'),
    path('change-password/', views.change_password, name='change_password'),
]