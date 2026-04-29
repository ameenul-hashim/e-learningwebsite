from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('pending/', views.pending_requests, name='pending_requests'),
    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('decline/<int:user_id>/', views.decline_user, name='decline_user'),
    path('users/', views.user_management, name='user_management'),
    path('toggle-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    
    path('add-subject/', views.add_subject, name='add_subject'),
    path('delete-subject/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    path('subject/<int:subject_id>/', views.subject_detail_admin, name='subject_detail_admin'),
    path('subject/<int:subject_id>/add-video/', views.add_video, name='add_video'),
    path('delete-video/<int:video_id>/', views.delete_video, name='delete_video'),
]
