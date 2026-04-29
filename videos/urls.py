from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('subject/<int:subject_id>/', views.subject_detail, name='subject_detail'),
]
