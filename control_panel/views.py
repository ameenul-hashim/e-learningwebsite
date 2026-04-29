from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import AccessRequest, User
from videos.models import Video, Category
from functools import wraps


def cp_admin_required(view_func):
    """
    Custom decorator: redirects to /control-panel/login/ if not staff.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('cp_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@cp_admin_required
def dashboard(request):
    """
    Main admin dashboard overview.
    """
    stats = {
        'total_users': User.objects.count(),
        'pending_requests': AccessRequest.objects.filter(status='pending').count(),
        'total_videos': Video.objects.count(),
        'total_categories': Category.objects.count(),
    }
    return render(request, 'control_panel/dashboard.html', {'stats': stats})


@cp_admin_required
def manage_requests(request):
    """
    Handle user access requests.
    """
    pending = AccessRequest.objects.filter(status='pending').order_by('-created_at')
    history = AccessRequest.objects.exclude(status='pending').order_by('-created_at')[:20]
    return render(request, 'control_panel/requests.html', {
        'pending': pending,
        'history': history
    })


@cp_admin_required
def approve_request(request, pk):
    """
    Approve an access request and create a user account.
    """
    access_req = get_object_or_404(AccessRequest, pk=pk)

    # Check if user already exists
    if User.objects.filter(email=access_req.email).exists():
        messages.error(request, f"User with email {access_req.email} already exists.")
    else:
        # Generate a simple username from email if not provided
        username = access_req.email.split('@')[0]
        password = User.objects.make_random_password()

        user = User.objects.create_user(
            username=username,
            email=access_req.email,
            password=password,
            is_verified=True
        )

        access_req.status = 'approved'
        access_req.save()

        # In a real app, you'd send an email here with credentials
        messages.success(request, f"Approved! Account created for {username}. Temp Password: {password}")

    return redirect('cp_requests')


@cp_admin_required
def decline_request(request, pk):
    """
    Decline an access request.
    """
    access_req = get_object_or_404(AccessRequest, pk=pk)
    access_req.status = 'declined'
    access_req.save()
    messages.info(request, f"Request from {access_req.name} declined.")
    return redirect('cp_requests')


@cp_admin_required
def manage_videos(request):
    """
    Manage video catalog.
    """
    videos = Video.objects.select_related('category').all().order_by('-created_at')
    categories = Category.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        youtube_url = request.POST.get('youtube_url')
        category_id = request.POST.get('category')

        if title and youtube_url:
            category = Category.objects.get(id=category_id) if category_id else None
            Video.objects.create(
                title=title,
                youtube_url=youtube_url,
                category=category
            )
            messages.success(request, f"Video '{title}' added successfully.")
            return redirect('cp_videos')

    return render(request, 'control_panel/videos.html', {
        'videos': videos,
        'categories': categories
    })


@cp_admin_required
def delete_video(request, pk):
    """
    Delete a video.
    """
    video = get_object_or_404(Video, pk=pk)
    video.delete()
    messages.warning(request, "Video removed.")
    return redirect('cp_videos')


@cp_admin_required
def manage_users(request):
    """
    Manage users (list, create, edit).
    """
    users = User.objects.all().order_by('-date_joined')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if username and email and password:
            if User.objects.filter(email=email).exists() or User.objects.filter(username=username).exists():
                messages.error(request, "User with this username or email already exists.")
            else:
                User.objects.create_user(username=username, email=email, password=password, is_verified=True)
                messages.success(request, f"User '{username}' created successfully.")
        return redirect('cp_users')

    return render(request, 'control_panel/users.html', {'users': users})


@cp_admin_required
def delete_user(request, pk):
    """
    Delete a user.
    """
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, "Cannot delete superuser.")
    else:
        user.delete()
        messages.warning(request, "User deleted.")
    return redirect('cp_users')


@cp_admin_required
def toggle_user_status(request, pk):
    """
    Block/Activate a user.
    """
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, "Cannot modify superuser status.")
    else:
        user.is_blocked = not user.is_blocked
        user.is_active = not user.is_blocked
        user.save()
        status = "blocked" if user.is_blocked else "activated"
        messages.success(request, f"User {user.username} has been {status}.")
    return redirect('cp_users')


@cp_admin_required
def manage_categories(request):
    """
    Manage categories/subjects.
    """
    categories = Category.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            Category.objects.create(name=name, description=description)
            messages.success(request, f"Subject '{name}' added successfully.")
            return redirect('cp_categories')

    return render(request, 'control_panel/categories.html', {'categories': categories})


@cp_admin_required
def delete_category(request, pk):
    """
    Delete a category/subject.
    """
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.warning(request, "Subject deleted.")
    return redirect('cp_categories')

