import logging
from celery import shared_task
from django.utils import timezone
from .models import Video, WatchHistory
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger('production.tasks')

@shared_task
def record_watch_event_async(user_id, video_id):
    """
    Background task to record a watch event without blocking the request.
    """
    try:
        user = User.objects.get(id=user_id)
        video = Video.objects.get(id=video_id)
        
        WatchHistory.objects.update_or_create(
            user=user,
            video=video,
            defaults={'watched_at': timezone.now()}
        )
        logger.info(f"Async: Recorded watch event for {user.username} - {video.title}")
    except Exception as e:
        logger.error(f"Error in record_watch_event_async: {str(e)}")

@shared_task
def aggregate_video_analytics():
    """
    Periodic task to aggregate video engagement metrics.
    """
    logger.info("Starting background analytics aggregation...")
    # Complex aggregation logic here
    pass
