from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from accounts.models import User
from videos.models import Subject, Video
from django.contrib import messages

def admin_check(u): return u.is_authenticated and u.is_staff

@user_passes_test(admin_check, login_url='login')
def admin_dashboard(request):
    data = {
        'total_users': User.objects.exclude(is_staff=True).count(),
        'pending_count': User.objects.filter(status='pending').count(),
        'active_count': User.objects.filter(is_active=True, is_staff=False).count(),
        'subjects': Subject.objects.all(),
    }
    return render(request, 'control_panel/dashboard.html', data)

@user_passes_test(admin_check, login_url='login')
def pending_requests(request):
    reqs = User.objects.filter(status='pending').order_by('-date_joined')
    return render(request, 'control_panel/pending.html', {'reqs': reqs})

@user_passes_test(admin_check, login_url='login')
def approve_user(request, uid):
    u = get_object_or_404(User, id=uid)
    u.status = 'approved'
    u.is_active = True
    u.save()
    messages.success(request, f"{u.username} approved.")
    return redirect('pending_requests')

@user_passes_test(admin_check, login_url='login')
def decline_user(request, uid):
    u = get_object_or_404(User, id=uid)
    u.status = 'blocked'
    u.is_active = False
    u.save()
    messages.warning(request, f"{u.username} declined.")
    return redirect('pending_requests')

@user_passes_test(admin_check, login_url='login')
def user_management(request):
    users = User.objects.exclude(is_staff=True).order_by('-date_joined')
    return render(request, 'control_panel/users.html', {'users': users})

@user_passes_test(admin_check, login_url='login')
def toggle_user(request, uid):
    u = get_object_or_404(User, id=uid)
    u.is_active = not u.is_active
    u.status = 'approved' if u.is_active else 'blocked'
    u.save()
    return redirect('user_management')

@user_passes_test(admin_check, login_url='login')
def delete_user(request, uid):
    u = get_object_or_404(User, id=uid)
    u.delete()
    return redirect('user_management')

# Subject CRUD
@user_passes_test(admin_check, login_url='login')
def subject_crud(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        desc = request.POST.get('description')
        Subject.objects.create(name=name, description=desc)
        return redirect('admin_dashboard')
    return redirect('admin_dashboard')

@user_passes_test(admin_check, login_url='login')
def delete_subject(request, sid):
    get_object_or_404(Subject, id=sid).delete()
    return redirect('admin_dashboard')

@user_passes_test(admin_check, login_url='login')
def add_video(request, sid):
    sub = get_object_or_404(Subject, id=sid)
    if request.method == 'POST':
        Video.objects.create(
            subject=sub,
            title=request.POST.get('title'),
            youtube_url=request.POST.get('url')
        )
    return redirect('admin_dashboard')
