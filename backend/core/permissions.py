from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    Assumes the model instance has an `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'user') and obj.user == request.user

class IsAnalysisOwner(permissions.BasePermission):
    """
    For nested objects like Feedback which have analysis.user instead of just user.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'analysis') and hasattr(obj.analysis, 'user'):
            return obj.analysis.user == request.user
        return False
