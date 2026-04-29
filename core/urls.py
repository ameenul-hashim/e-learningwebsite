from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def landing(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_staff else 'dashboard')
    return redirect('login')

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', landing, name='landing'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('videos.urls')),
    path('control-panel/', include('control_panel.urls')),
]
