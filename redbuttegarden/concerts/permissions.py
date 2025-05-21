from rest_framework import permissions

class IsInAPIGroup(permissions.BasePermission):
    """
    Allows access only to users in the 'API' group.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='API').exists()
