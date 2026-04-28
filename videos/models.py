import re
from django.db import models
from django.conf import settings

class Category(models.Model):
    """
    Model for video categories.
    """
    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Video(models.Model):
    """
    Model for storing YouTube video links with category grouping.
    """
    title = models.CharField(max_length=255, db_index=True)
    youtube_url = models.URLField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='videos', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def youtube_id(self):
        """
        Extracts the 11-character YouTube video ID.
        """
        regex_patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'embed\/([0-9A-Za-z_-]{11})',
        ]
        for pattern in regex_patterns:
            match = re.search(pattern, self.youtube_url)
            if match:
                return match.group(1)
        return None

    @property
    def embed_url(self):
        video_id = self.youtube_id
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        return self.youtube_url

    @property
    def thumbnail_url(self):
        video_id = self.youtube_id
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        return ""

class WatchHistory(models.Model):
    """
    Tracks which videos a user has watched.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Watch Histories"
        unique_together = ('user', 'video')
        ordering = ['-watched_at']

    def __str__(self):
        return f"{self.user.username} watched {self.video.title}"
