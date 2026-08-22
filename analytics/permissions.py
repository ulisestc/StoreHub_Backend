from rest_framework import permissions

class IsPremiumStore(permissions.BasePermission):
    """
    Allows access only to users whose store is premium.
    """
    message = "Tu tienda debe ser Premium para acceder a esta función."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.store and
            request.user.store.is_premium
        )
