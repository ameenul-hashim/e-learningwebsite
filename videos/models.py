from django.db import models
import re

class Subject(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Video(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=255)
    youtube_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def youtube_id(self):
        regex_patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'embed\/([0-9A-Za-z_-]{11})',
        ]
        for pattern in regex_patterns:
            match = re.search(pattern, self.youtube_url)
            if match: return match.group(1)
        return None

    @property
    def embed_url(self):
        video_id = self.youtube_id
        return f"https://www.youtube.com/embed/{video_id}" if video_id else self.youtube_url