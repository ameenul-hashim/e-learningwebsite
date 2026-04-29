from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def landing_router(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    return redirect('login')

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', landing_router, name='landing'),
    path('auth/', include('accounts.urls')),
    path('dashboard/', include('videos.urls')),
    path('control-panel/', include('control_panel.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
