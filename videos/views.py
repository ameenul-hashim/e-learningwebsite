from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subject, Video

@login_required
def dashboard_view(request):
    subjects = Subject.objects.all()
    return render(request, 'videos/dashboard.html', {'subjects': subjects})

@login_required
def subject_detail_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    videos = subject.videos.all()
    return render(request, 'videos/subject_detail.html', {'subject': subject, 'videos': videos})

@login_required
def video_detail_view(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    return render(request, 'videos/video_detail.html', {'video': video})
