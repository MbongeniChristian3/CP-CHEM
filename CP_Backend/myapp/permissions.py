# myapp/permissions.py
from rest_framework import permissions

# ... (your existing permission classes)

class IsCEOOrChairman(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        # Check authentication and profile existence first
        if not user.is_authenticated or not hasattr(user, 'profile'):
            return False
        return user.profile.role in ['ceo', 'chairman']

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        # Check authentication and profile existence first
        if not user.is_authenticated or not hasattr(user, 'profile'):
            return False
        return user.profile.role == 'manager'

class IsCashier(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        # Check authentication and profile existence first
        if not user.is_authenticated or not hasattr(user, 'profile'):
            return False
        return user.profile.role == 'cashier'


class HasWarehouseAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        
        # Check if user is authenticated first
        if not user.is_authenticated:
            return False
        
        # Check if user has a profile
        if not hasattr(user, 'profile'):
            return False
        
        # Allow all CEOs and Chairmen to see everything
        if user.profile.role in ['ceo', 'chairman']:
            return True
        
        # Only managers, cashiers, and dispatchers should access this view
        return user.profile.role in ['manager', 'cashier', 'dispatch']

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Check if user is authenticated first
        if not user.is_authenticated:
            return False
        
        # Check if user has a profile
        if not hasattr(user, 'profile'):
            return False
        
        # A CEO or Chairman has full access to all objects
        if user.profile.role in ['ceo', 'chairman']:
            return True
            
        # Managers, Cashiers, and Dispatchers can only access objects in their own warehouse.
        if hasattr(obj, 'warehouse') and hasattr(user.profile, 'warehouse'):
            return obj.warehouse == user.profile.warehouse
        
        # Default: deny access
        return False# myapp/permissions.py
from rest_framework import permissions

class HasWarehouseAccess(permissions.BasePermission):
    """
    Custom permission to check if user has warehouse access.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated first
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Check if user has a profile
        if not hasattr(user, 'profile'):
            return False
        
        # CEO and Chairman have access to everything
        if user.profile.role in ['ceo', 'chairman']:
            return True
        
        # Other users need to have a warehouse assigned
        if user.profile.warehouse:
            return True
        
        # Default: deny access
        return False

    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated first
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Check if user has a profile
        if not hasattr(user, 'profile'):
            return False
        
        # CEO and Chairman have access to all objects
        if user.profile.role in ['ceo', 'chairman']:
            return True
        
        # For other users, check if object belongs to their warehouse
        if hasattr(obj, 'warehouse') and user.profile.warehouse:
            return obj.warehouse == user.profile.warehouse
        
        # Default: deny access
        return False