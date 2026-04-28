import logging
from django.core.cache import cache
from django.db.models import Prefetch
from ..models import Video, Category, WatchHistory

logger = logging.getLogger(__name__)

class VideoService:
    @staticmethod
    def get_categorized_videos(user):
        """
        Fetches categorized videos with prefetching and logging.
        """
        logger.info(f"Fetching categorized videos for user: {user.username}")
        
        # Try to get from cache if appropriate, but usually dashboard is dynamic per user history
        categories = Category.objects.prefetch_related(
            Prefetch('videos', queryset=Video.objects.order_by('-created_at'))
        ).all()
        
        return categories

    @staticmethod
    def get_user_watch_history(user, limit=10):
        """
        Fetches the watch history for a specific user.
        """
        return WatchHistory.objects.filter(user=user).select_related('video')[:limit]

    @staticmethod
    def record_watch_event(user, video):
        """
        Records a watch event. Safe against worker/broker failures.
        """
        from ..tasks import record_watch_event_async
        from core.utils import safe_task_delay
        
        logger.info(f"Initiating safe watch event record for {user.username}")
        
        # Use safe helper to manage async/sync execution
        safe_task_delay(record_watch_event_async, user.id, video.id)
        
        return True
