from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# from rest_framework.routers import DefaultRouter
# from videos.api_views import VideoViewSet, CategoryViewSet

def health_check(request):
    from django.db import connections
    from django.db.utils import OperationalError
    from django.core.cache import cache
    
    # Check Database
    db_conn = connections['default']
    try:
        db_conn.cursor()
        db_status = "connected"
    except OperationalError:
        db_status = "unavailable"
    
    # Check Cache (Redis)
    try:
        cache.set('health_check', 'ok', timeout=10)
        cache_val = cache.get('health_check')
        cache_status = "connected" if cache_val == 'ok' else "unavailable"
    except Exception:
        cache_status = "unavailable"
    
    status_code = 200 if db_status == "connected" else 503
    
    return JsonResponse({
        "status": "healthy" if (db_status == "connected" and cache_status == "connected") else "degraded",
        "database": db_status,
        "cache": cache_status
    }, status=status_code)

# router = DefaultRouter()
# router.register(r'videos', VideoViewSet)
# router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('', include('accounts.urls')),
    path('', include('videos.urls')),
    path('', include('control_panel.urls')),
    
    # Password Reset URLs
    path('accounts/', include('django.contrib.auth.urls')),
    
    # API Endpoints
    # path('api/', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
