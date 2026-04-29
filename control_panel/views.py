from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from accounts.models import User
from videos.models import Subject, Video

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='admin_login')(view_func)

def admin_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                auth_login(request, user)
                return redirect('admin_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'control_panel/login.html', {'form': form})

@admin_required
def admin_dashboard(request):
    subjects = Subject.objects.all()
    users = User.objects.exclude(is_staff=True)
    return render(request, 'control_panel/dashboard.html', {'subjects': subjects, 'users': users})

@admin_required
def admin_logout(request):
    auth_logout(request)
    return redirect('admin_login')

@admin_required
def add_subject(request):
    if request.method == 'POST':
        Subject.objects.create(name=request.POST.get('name'))
    return redirect('admin_dashboard')

@admin_required
def add_video(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        Video.objects.create(subject=subject, title=request.POST.get('title'), youtube_url=request.POST.get('youtube_url'))
    return redirect('admin_dashboard')
