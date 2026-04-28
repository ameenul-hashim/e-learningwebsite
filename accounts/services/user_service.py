import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def validate_user_access(user):
        """
        Validates if a user is allowed to access premium content.
        """
        if not user.is_verified:
            logger.warning(f"Unverified access attempt by {user.username}")
            return False, "Your account is not yet verified."
            
        if user.is_blocked:
            logger.warning(f"Blocked access attempt by {user.username}")
            return False, "Your account has been blocked."
            
        if user.access_expires and user.access_expires < timezone.now().date():
            logger.info(f"Expired access attempt by {user.username}")
            return False, "Your access has expired."
            
        return True, ""
