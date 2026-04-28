from django.urls import path
from .views import landing_page, RestrictedLoginView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', landing_page, name='landing'),
    path('login/', RestrictedLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='landing'), name='logout'),
]
