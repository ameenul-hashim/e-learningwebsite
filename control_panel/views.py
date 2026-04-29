from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from accounts.models import User
from videos.models import Subject, Video
from django.contrib import messages

def admin_check(u): return u.is_authenticated and u.is_staff

@user_passes_test(admin_check, login_url='login')
def admin_dashboard(request):
    data = {
        'total': User.objects.exclude(is_staff=True).count(),
        'pending': User.objects.filter(is_active=False, is_staff=False).count(),
        'subjects': Subject.objects.all(),
    }
    return render(request, 'control_panel/dashboard.html', data)

@user_passes_test(admin_check, login_url='login')
def pending_list(request):
    return render(request, 'control_panel/pending.html', {'reqs': User.objects.filter(is_active=False, is_staff=False)})

@user_passes_test(admin_check, login_url='login')
def approve_user(request, uid):
    u = get_object_or_404(User, id=uid); u.is_active = True; u.status = 'approved'; u.save()
    messages.success(request, f"{u.username} approved."); return redirect('pending_list')

@user_passes_test(admin_check, login_url='login')
def decline_user(request, uid):
    u = get_object_or_404(User, id=uid); u.status = 'blocked'; u.save()
    messages.error(request, f"{u.username} declined."); return redirect('pending_list')

@user_passes_test(admin_check, login_url='login')
def user_list(request):
    return render(request, 'control_panel/users.html', {'users': User.objects.exclude(is_staff=True)})

@user_passes_test(admin_check, login_url='login')
def toggle_user(request, uid):
    u = get_object_or_404(User, id=uid); u.is_active = not u.is_active
    u.status = 'approved' if u.is_active else 'blocked'; u.save()
    return redirect('user_list')

@user_passes_test(admin_check, login_url='login')
def delete_user(request, uid):
    get_object_or_404(User, id=uid).delete(); return redirect('user_list')

@user_passes_test(admin_check, login_url='login')
def add_subject(request):
    if request.method == 'POST': Subject.objects.create(name=request.POST.get('name'), description=request.POST.get('desc'))
    return redirect('admin_dashboard')

@user_passes_test(admin_check, login_url='login')
def add_video(request, sid):
    s = get_object_or_404(Subject, id=sid)
    if request.method == 'POST': Video.objects.create(subject=s, title=request.POST.get('title'), youtube_url=request.POST.get('url'))
    return redirect('admin_dashboard')
