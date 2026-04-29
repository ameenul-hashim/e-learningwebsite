from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from accounts.models import User
from videos.models import Subject, Video
from django.db.models import Count

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='admin_login')(view_func)

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                auth_login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Access denied. Not an administrator.")
        else:
            messages.error(request, "Invalid administrator credentials.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'control_panel/login.html', {'form': form})

@admin_required
def admin_logout(request):
    auth_logout(request)
    messages.info(request, "Logged out from Admin Panel.")
    return redirect('admin_login')

@admin_required
def admin_dashboard(request):
    total_users = User.objects.exclude(is_staff=True).count()
    pending_approvals = User.objects.filter(status='pending').count()
    active_users = User.objects.filter(status='approved', is_active=True).count()
    
    subjects = Subject.objects.annotate(video_count=Count('videos'))
    
    context = {
        'total_users': total_users,
        'pending_approvals': pending_approvals,
        'active_users': active_users,
        'subjects': subjects,
    }
    return render(request, 'control_panel/dashboard.html', context)

@admin_required
def pending_requests(request):
    requests = User.objects.filter(status='pending').order_by('-date_joined')
    return render(request, 'control_panel/pending_requests.html', {'requests': requests})

@admin_required
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.status = 'approved'
    user.is_active = True
    user.save()
    messages.success(request, f"User {user.username} approved.")
    return redirect('pending_requests')

@admin_required
def decline_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.status = 'blocked' # Or we could delete, but prompt says "Decline -> keep user.is_active = False"
    user.is_active = False
    user.save()
    messages.warning(request, f"User {user.username} declined.")
    return redirect('pending_requests')

@admin_required
def user_management(request):
    users = User.objects.exclude(is_staff=True).order_by('-date_joined')
    return render(request, 'control_panel/user_management.html', {'users': users})

@admin_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.status == 'blocked':
        user.status = 'approved'
        user.is_active = True
    else:
        user.status = 'blocked'
        user.is_active = False
    user.save()
    return redirect('user_management')

@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted.")
    return redirect('user_management')

# Subject and Video CRUD
@admin_required
def add_subject(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        Subject.objects.create(name=name, description=description)
        messages.success(request, "Subject added.")
    return redirect('admin_dashboard')

@admin_required
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted.")
    return redirect('admin_dashboard')

@admin_required
def add_video(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        youtube_url = request.POST.get('youtube_url')
        Video.objects.create(subject=subject, title=title, youtube_url=youtube_url)
        messages.success(request, "Video added.")
    return redirect('subject_detail_admin', subject_id=subject_id)

@admin_required
def subject_detail_admin(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    videos = subject.videos.all()
    return render(request, 'control_panel/subject_detail.html', {'subject': subject, 'videos': videos})

@admin_required
def delete_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    subject_id = video.subject.id
    video.delete()
    messages.success(request, "Video deleted.")
    return redirect('subject_detail_admin', subject_id=subject_id)
