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
    def __str__(self): return self.title
    @property
    def embed_url(self):
        m = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', self.youtube_url)
        return f"https://www.youtube.com/embed/{m.group(1)}" if m else self.youtube_url
