from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    status = models.CharField(max_length=20, default='approved') # default to approved to 'cancel constraints'
    
    def __str__(self):
        return self.username
