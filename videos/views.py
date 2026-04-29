from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import cache_page
from .models import Video, DownloadLog
from .services.video_service import VideoService
from accounts.services.user_service import UserService
from ratelimit.decorators import ratelimit

@login_required
@cache_page(60 * 15)
def video_dashboard(request):
    """
    Refactored Dashboard using Service Layer.
    """
    is_allowed, message = UserService.validate_user_access(request.user)
    if not is_allowed:
        raise PermissionDenied(message)
    
    query = request.GET.get('q')
    
    if query:
        videos = Video.objects.filter(title__icontains=query).select_related('category').order_by('-created_at')
        return render(request, 'videos/search_results.html', {'videos': videos, 'query': query})
    
    categories = VideoService.get_categorized_videos(request.user)
    history = VideoService.get_user_watch_history(request.user)
    
    return render(request, 'videos/dashboard.html', {
        'categories': categories,
        'history': history
    })

@login_required
@ratelimit(key='user', rate='10/m', block=True)
def watch_video(request, video_id):
    """
    Refactored Watch View using Service Layer.
    """
    is_allowed, message = UserService.validate_user_access(request.user)
    if not is_allowed:
        raise PermissionDenied(message)
        
    video = get_object_or_404(Video.objects.select_related('category'), id=video_id)
    
    VideoService.record_watch_event(request.user, video)
    
    # Log video access for tracking
    DownloadLog.objects.create(user=request.user, video=video)
    
    return render(request, 'videos/watch.html', {'video': video})

@login_required
def subject_videos(request, category_id):
    """
    Shows videos within a specific subject/category.
    """
    is_allowed, message = UserService.validate_user_access(request.user)
    if not is_allowed:
        raise PermissionDenied(message)
    
    from .models import Category
    category = get_object_or_404(Category, id=category_id)
    videos = Video.objects.filter(category=category).order_by('-created_at')
    
    return render(request, 'videos/subject_videos.html', {
        'category': category,
        'videos': videos
    })

