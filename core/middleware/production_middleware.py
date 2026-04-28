import logging
import time
from django.http import JsonResponse, HttpResponseServerError
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('production.middleware')

class ProductionErrorMiddleware:
    """
    Catches unhandled exceptions and logs them properly.
    Returns JSON for API requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
            
            if request.path.startswith('/api/'):
                return JsonResponse({
                    "error": "Internal Server Error",
                    "message": "A technical error occurred. Please try again later."
                }, status=500)
            
            return HttpResponseServerError("Internal Server Error. Please contact support.")

class RateLimitMiddleware:
    """
    Basic rate limiting using Django's cache.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/') or request.path == '/login/':
            ip = self.get_client_ip(request)
            cache_key = f"rl_{ip}_{request.path}"
            
            requests = cache.get(cache_key, 0)
            if requests >= 60:  # 60 requests per minute
                logger.warning(f"Rate limit exceeded for IP: {ip} on path: {request.path}")
                return JsonResponse({"error": "Rate limit exceeded. Please wait a minute."}, status=429)
            
            cache.set(cache_key, requests + 1, 60)
            
        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class RequestLoggingMiddleware:
    """
    Logs duration and status of API requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        if request.path.startswith('/api/'):
            logger.info(
                f"API Request: {request.method} {request.path} | Status: {response.status_code} | Duration: {duration:.2f}s"
            )
        
        return response
class NoCacheMiddleware:
    """
    Prevents browser caching for authenticated users.
    Ensures that clicking 'Back' after logout doesn't show sensitive data.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response
