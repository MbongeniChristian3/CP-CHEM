from django.db import models
from django.contrib.auth.models import User

class MyModel(models.Model):
    # Your existing model fields
    name = models.CharField(max_length=255)
    description = models.TextField(default='') # Added an empty string as a default

class Profile(models.Model):
    CEO = 'ceo'
    MANAGER = 'manager'
    CASHIER = 'cashier'
    CHAIRMAN = 'chairman'
    
    ROLE_CHOICES = (
        (CEO, 'CEO'),
        (MANAGER, 'Manager'),
        (CASHIER, 'Cashier'),
        (CHAIRMAN, 'Chairman'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CASHIER)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"