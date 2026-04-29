from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('subject/<int:subject_id>/', views.subject_detail_view, name='subject_detail'),
    path('video/<int:video_id>/', views.video_detail_view, name='video_detail'),
]
