from rest_framework import permissions

class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow creators of an object to edit or delete it.
    Read permissions (GET, HEAD, OPTIONS) are allowed for all authenticated users.
    """
    
    def has_permission(self, request, view):
        # Ensure the user is logged in for any operation (read or write)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to anyone who passed has_permission.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions (PUT, PATCH, DELETE) are only allowed if:
        # The PK of the object's creator matches the PK of the request user.
        if request.user.is_authenticated:
            return obj.creator.pk == request.user.pk
        
        return False 