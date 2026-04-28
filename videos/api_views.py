from rest_framework import viewsets, permissions
from .models import Video, Category
from .serializers import VideoSerializer, CategorySerializer

class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows videos to be viewed.
    """
    queryset = Video.objects.all().select_related('category').order_by('-created_at')
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.filter(title__icontains=query)
        return queryset

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows categories to be viewed.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
