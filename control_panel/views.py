from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.models import AccessRequest, User
from videos.models import Video, Category
from django.utils import timezone

@staff_member_required
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

@staff_member_required
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

@staff_member_required
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

@staff_member_required
def decline_request(request, pk):
    """
    Decline an access request.
    """
    access_req = get_object_or_404(AccessRequest, pk=pk)
    access_req.status = 'declined'
    access_req.save()
    messages.info(request, f"Request from {access_req.name} declined.")
    return redirect('cp_requests')

@staff_member_required
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

@staff_member_required
def delete_video(request, pk):
    """
    Delete a video.
    """
    video = get_object_or_404(Video, pk=pk)
    video.delete()
    messages.warning(request, "Video removed.")
    return redirect('cp_videos')
