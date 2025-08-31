from rest_framework import permissions

class IsCEOOrChairman(permissions.BasePermission):
    """
    Custom permission to allow only CEO or Chairman to manage all branches.
    """
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.profile.role in ['ceo', 'chairman'])

class IsManager(permissions.BasePermission):
    """
    Custom permission to allow only Managers to access their warehouse.
    """
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.profile.role == 'manager')

class IsCashier(permissions.BasePermission):
    """
    Custom permission to allow only Cashiers to access their warehouse.
    """
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.profile.role == 'cashier')