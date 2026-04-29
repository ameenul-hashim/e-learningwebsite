from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model for EduStream platform.
    """
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    proof_file = models.FileField(upload_to='proofs/', blank=True, null=True)
    
    # is_active = False by default for signups
    # we can use a custom field to track approval status if needed, 
    # but is_active is enough to block login.
    # To distinguish between "Pending" and "Blocked", we can use a status field.
    
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('blocked', 'Blocked'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return self.username
