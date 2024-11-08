from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.pagination import CommonPagination
from api.permissions import IsAuthenticated
from common.constants import (ERROR_ALREADY_SUBSCRIBED,
                              ERROR_CANNOT_SUBSCRIBE_TO_SELF,
                              ERROR_SUBSCRIPTION_NOT_FOUND, URL_AVATAR_PATH,
                              URL_CURRENT_USER_PATH, URL_SUBSCRIBE_PATH,
                              URL_SUBSCRIPTIONS_PATH)
from common.serializers import UserSerializer
from .models import Subscription
from .serializers import SubscriptionUserSerializer, UserAvatarSerializer

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CommonPagination

    @action(detail=False, methods=['get'], url_path=URL_CURRENT_USER_PATH,
            permission_classes=[IsAuthenticated])
    def me(self, request):
        """Возвращает данные текущего авторизованного пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path=URL_AVATAR_PATH,
            permission_classes=[IsAuthenticated])
    def update_avatar(self, request):
        """Обновляет или удаляет аватар пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user, data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
            self.perform_update(serializer)
            return Response(serializer.data)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated], url_path=URL_SUBSCRIBE_PATH)
    def subscribe(self, request, id=None):
        """Осуществляет подписку на или отписку от другого пользователя."""
        user = request.user
        if user.id == int(id):
            return Response({'detail': ERROR_CANNOT_SUBSCRIBE_TO_SELF},
                            status=status.HTTP_400_BAD_REQUEST)

        user_to_subscribe = get_object_or_404(User, id=id)

        if request.method == 'POST':
            _, created = Subscription.objects.get_or_create(
                user=user, subscribed_to=user_to_subscribe
            )
            if created:
                serializer = SubscriptionUserSerializer(
                    user_to_subscribe, context={'request': request})
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                {'detail': ERROR_ALREADY_SUBSCRIBED},
                status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=user, subscribed_to=user_to_subscribe
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': ERROR_SUBSCRIPTION_NOT_FOUND},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=URL_SUBSCRIPTIONS_PATH)
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        subscriptions = Subscription.objects.filter(
            user=request.user
        ).select_related('subscribed_to')
        subscribed_users = [sub.subscribed_to for sub in subscriptions]

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(subscribed_users, request)

        serializer = SubscriptionUserSerializer(
            page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
