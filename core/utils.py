import logging
from django.conf import settings

logger = logging.getLogger('production.utils')

def safe_task_delay(task, *args, **kwargs):
    """
    Safely executes a Celery task. 
    If Celery is not configured or fails, it can fall back to sync execution.
    """
    try:
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', True):
            # Run synchronously in dev or if Redis is missing
            return task(*args, **kwargs)
        else:
            # Run asynchronously
            return task.delay(*args, **kwargs)
    except Exception as e:
        logger.error(f"Task Execution Failed for {task.__name__}: {str(e)}. Falling back to sync.")
        try:
            return task(*args, **kwargs)
        except Exception as sync_e:
            logger.critical(f"Critical Failure: Sync fallback also failed for {task.__name__}: {str(e)}")
            return None
