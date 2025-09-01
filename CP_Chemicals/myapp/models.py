from django.db import models
from django.contrib.auth.models import User

# This is the new model for your warehouses or branches.
class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class MyModel(models.Model):
    # Your existing model fields
    name = models.CharField(max_length=255)
    description = models.TextField(default='')
    
    # New: Link this model to a warehouse.
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Profile(models.Model):
    CEO = 'ceo'
    MANAGER = 'manager'
    CASHIER = 'cashier'
    CHAIRMAN = 'chairman'
    DISPATCH = 'dispatch'
    
    ROLE_CHOICES = (
        (CEO, 'CEO'),
        (MANAGER, 'Manager'),
        (CASHIER, 'Cashier'),
        (CHAIRMAN, 'Chairman'),
        (DISPATCH, 'Dispatch'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CASHIER)
    
    # New: Link a user's profile to a specific warehouse.
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"