from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


def relationship_action_decorator(url_path):
    """Декоратор для создания эндпоинта с POST и DELETE методами.

    Позволяет задать URL для эндпоинта и применяет права доступа
    только для авторизованных пользователей.
    """
    def decorator(func):
        return action(detail=True, methods=['post', 'delete'],
                      url_path=url_path,
                      permission_classes=[IsAuthenticated])(func)
    return decorator
