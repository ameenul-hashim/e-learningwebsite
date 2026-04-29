from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model for the e-learning platform.
    """
    email = models.EmailField(unique=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=True)
    last_active = models.DateTimeField(null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
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
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request from {self.name} ({self.email})"

class AdminAuditLog(models.Model):
    """
    Tracks administrative actions for accountability.
    """
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=255, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    details = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.admin_user} - {self.action} - {self.timestamp}"

