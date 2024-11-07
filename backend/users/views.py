from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.pagination import CommonPagination
from api.permissions import IsAuthenticated
from common.serializers import UserSerializer
from .models import Subscription
from .serializers import SubscriptionUserSerializer, UserAvatarSerializer

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CommonPagination

    @action(detail=False, methods=['get'], url_path='me',
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def update_avatar(self, request):
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
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        if user.id == int(id):
            return Response({'detail': 'Вы не можете подписаться на себя.'},
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
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=user, subscribed_to=user_to_subscribe
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': 'Подписка не найдена.'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(
            user=request.user
        ).select_related('subscribed_to')
        subscribed_users = [sub.subscribed_to for sub in subscriptions]

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(subscribed_users, request)

        serializer = SubscriptionUserSerializer(
            page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
