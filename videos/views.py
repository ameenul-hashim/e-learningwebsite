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
    return render(request, 'videos/subject_detail.html', {'subject': subject})

# urls.py content
from django.urls import path
from . import views
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('subject/<int:subject_id>/', views.subject_detail, name='subject_detail'),
]
