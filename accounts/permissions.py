# from rest_framework.permissions import BasePermission

# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'admin'
    
#     class IsUser(BasePermission):
#         def has_permission(self, request, view):
#             return request.user.is_authenticated and request.user.role == 'user'
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Allows access only to admin users (is_staff=True).
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user.role, 'name', '').lower() == 'admin')


class IsUser(BasePermission):
    """
    Allows access only to normal authenticated users (is_staff=False).
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user.role, 'name', '').lower() == 'user')
