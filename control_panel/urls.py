from django.urls import path
from . import views
from .auth_views import cp_login_view, cp_logout_view

urlpatterns = [
    path('control-panel/login/', cp_login_view, name='cp_login'),
    path('control-panel/logout/', cp_logout_view, name='cp_logout'),
    path('control-panel/', views.dashboard, name='cp_dashboard'),
    path('control-panel/requests/', views.manage_requests, name='cp_requests'),
    path('control-panel/requests/approve/<int:pk>/', views.approve_request, name='cp_approve'),
    path('control-panel/requests/reject/<int:pk>/', views.decline_request, name='cp_reject'),
    path('control-panel/create-user/<int:request_id>/', views.create_user_from_request, name='cp_create_user_from_request'),
    path('control-panel/videos/', views.manage_videos, name='cp_videos'),
    path('control-panel/videos/delete/<int:pk>/', views.delete_video, name='cp_delete_video'),
    
    # User Management
    path('control-panel/users/', views.manage_users, name='cp_users'),
    path('control-panel/users/delete/<int:pk>/', views.delete_user, name='cp_delete_user'),
    path('control-panel/users/toggle/<int:pk>/', views.toggle_user_status, name='cp_toggle_user'),
    path('control-panel/users/resend/<int:pk>/', views.resend_credentials, name='cp_resend_credentials'),

    # Category/Subject Management
    path('control-panel/categories/', views.manage_categories, name='cp_categories'),
    path('control-panel/categories/delete/<int:pk>/', views.delete_category, name='cp_delete_category'),
]
