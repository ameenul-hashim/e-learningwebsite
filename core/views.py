from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

def health_check(request):
    """
    Production health check endpoint.
    """
    health = {
        "status": "ok",
        "database": "disconnected",
        "cache": "inactive",
    }
    
    # Check Database
    try:
        connection.ensure_connection()
        health["database"] = "connected"
    except Exception:
        health["status"] = "error"
        
    # Check Cache
    try:
        cache.set("health_test", "ok", 10)
        if cache.get("health_test") == "ok":
            health["cache"] = "active"
    except Exception:
        health["status"] = "error"
        
    status_code = 200 if health["status"] == "ok" else 500
    return JsonResponse(health, status=status_code)
