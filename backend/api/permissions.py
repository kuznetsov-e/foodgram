from rest_framework import permissions


class IsAuthenticatedOrOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает доступ только владельцу объекта
    или для безопасных методов запроса.
    """

    def has_permission(self, request, view):
        return request.method != 'POST' or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and obj.author == request.user))


class IsAuthenticated(permissions.BasePermission):
    """Разрешает доступ только аутентифицированным пользователям."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
