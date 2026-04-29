from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('pending/', views.pending_requests, name='pending_requests'),
    path('approve/<int:uid>/', views.approve_user, name='approve_user'),
    path('decline/<int:uid>/', views.decline_user, name='decline_user'),
    path('users/', views.user_management, name='user_management'),
    path('toggle/<int:uid>/', views.toggle_user, name='toggle_user'),
    path('delete-user/<int:uid>/', views.delete_user, name='delete_user'),
    path('subject/add/', views.subject_crud, name='add_subject'),
    path('subject/delete/<int:sid>/', views.delete_subject, name='delete_subject'),
    path('subject/<int:sid>/video/add/', views.add_video, name='add_video_admin'),
]
