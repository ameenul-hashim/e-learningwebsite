from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model for the e-learning platform.
    """
    email = models.EmailField(unique=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    access_expires = models.DateField(null=True, blank=True, help_text="User access will be revoked after this date.")

    def __str__(self):
        return self.username

class AccessRequest(models.Model):
    """
    Model to handle user access requests for the platform.
    """
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20)
    proof = models.FileField(upload_to='proofs/')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request from {self.name} ({self.email})"
