from django.db import models
import re

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    def __str__(self): return self.name

class Video(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    youtube_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self): return self.title

    @property
    def embed_url(self):
        # Extract ID from various YT formats
        regex = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
        match = re.search(regex, self.youtube_url)
        if match:
            return f"https://www.youtube.com/embed/{match.group(1)}"
        return self.youtube_url
