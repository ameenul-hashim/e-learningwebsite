from django.urls import path
from .views import video_dashboard, watch_video, subject_videos

urlpatterns = [
    path('dashboard/', video_dashboard, name='dashboard'),
    path('watch/<int:video_id>/', watch_video, name='watch_video'),
    path('subject/<int:category_id>/', subject_videos, name='subject_videos'),
]
