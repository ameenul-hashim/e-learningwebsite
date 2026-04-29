import logging
import threading
from django.conf import settings

logger = logging.getLogger('production.utils')

def safe_task_delay(task, *args, **kwargs):
    """
    Safely executes a task using threading for background processing.
    """
    try:
        # Instead of Celery, we use a simple thread for now
        # This keeps the system lightweight and free-hosting compatible
        def run_task():
            try:
                task(*args, **kwargs)
            except Exception as e:
                logger.error(f"Async Thread Failure for {task.__name__}: {str(e)}")

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        logger.error(f"Failed to start thread for {task.__name__}: {str(e)}. Falling back to sync.")
        try:
            return task(*args, **kwargs)
        except Exception as sync_e:
            logger.critical(f"Critical Failure: Sync fallback also failed for {task.__name__}: {str(sync_e)}")
            return None
