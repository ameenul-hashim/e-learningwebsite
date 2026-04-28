from django.urls import path
from .views import video_dashboard, watch_video

urlpatterns = [
    path('dashboard/', video_dashboard, name='dashboard'),
    path('watch/<int:video_id>/', watch_video, name='watch_video'),
]
