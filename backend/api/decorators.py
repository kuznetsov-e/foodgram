from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


def relationship_action_decorator(url_path):
    def decorator(func):
        return action(detail=True, methods=['post', 'delete'],
                      url_path=url_path,
                      permission_classes=[IsAuthenticated])(func)
    return decorator
