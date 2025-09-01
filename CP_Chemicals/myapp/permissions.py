# myapp/permissions.py
from rest_framework import permissions

# ... (your existing permission classes)

class IsCEOOrChairman(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.profile.role in ['ceo', 'chairman'])

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.profile.role == 'manager')

class IsCashier(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.profile.role == 'cashier')


class HasWarehouseAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow all CEOs and Chairmen to see everything
        user = request.user
        if user.profile.role in ['ceo', 'chairman']:
            return True
        
        # Only managers, cashiers, and dispatchers should access this view
        return user.is_authenticated and (user.profile.role in ['manager', 'cashier', 'dispatch'])

    def has_object_permission(self, request, view, obj):
        # A CEO or Chairman has full access to all objects
        user = request.user
        if user.profile.role in ['ceo', 'chairman']:
            return True
            
        # Managers, Cashiers, and Dispatchers can only access objects in their own warehouse.
        return obj.warehouse == user.profile.warehouse