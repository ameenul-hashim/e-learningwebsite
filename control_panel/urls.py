from django.urls import path
from . import views

urlpatterns = [
    path('control-panel/', views.dashboard, name='cp_dashboard'),
    path('control-panel/requests/', views.manage_requests, name='cp_requests'),
    path('control-panel/requests/approve/<int:pk>/', views.approve_request, name='cp_approve'),
    path('control-panel/requests/decline/<int:pk>/', views.decline_request, name='cp_decline'),
    path('control-panel/videos/', views.manage_videos, name='cp_videos'),
    path('control-panel/videos/delete/<int:pk>/', views.delete_video, name='cp_delete_video'),
]
