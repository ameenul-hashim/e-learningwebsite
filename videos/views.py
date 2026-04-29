from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subject, Video

@login_required
def dashboard(request):
    subjects = Subject.objects.all()
    return render(request, 'videos/dashboard.html', {'subjects': subjects})

@login_required
def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    videos = subject.videos.all()
    return render(request, 'videos/subject_detail.html', {'subject': subject, 'videos': videos})
