from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subject

@login_required
def dashboard(request):
    return render(request, 'videos/dashboard.html', {'subjects': Subject.objects.all()})

@login_required
def subject_detail(request, sid):
    return render(request, 'videos/subject_detail.html', {'subject': get_object_or_404(Subject, id=sid)})
