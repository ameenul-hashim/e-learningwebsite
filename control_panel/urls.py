from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('add-subject/', views.add_subject, name='add_subject'),
    path('add-video/<int:subject_id>/', views.add_video, name='add_video'),
]
