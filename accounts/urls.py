from django.urls import path
from .views import landing_page, RestrictedLoginView, force_password_change
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', landing_page, name='landing'),
    path('login/', RestrictedLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='landing'), name='logout'),
    path('force-password-change/', force_password_change, name='force_password_change'),
    # path('setup-password/<uidb64>/<token>/', password_setup_view, name='password_setup'),
]
