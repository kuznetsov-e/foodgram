from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissions import IsAuthenticated
from .models import Subscription
from .serializers import SubscriptionUserSerializer, UserSerializer

User = get_user_model()


class UserAvatarUpdateView(generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()

        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        user = request.user
        user_to_subscribe = User.objects.get(
            pk=pk)

        if request.method == 'POST':
            _, created = Subscription.objects.get_or_create(
                user=user, subscribed_to=user_to_subscribe
            )
            if created:
                serializer = UserSerializer(
                    user_to_subscribe, context={'request': request})
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            raise ValidationError(
                {'detail': 'Вы уже подписаны на этого пользователя.'})

        elif request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=user, subscribed_to=user_to_subscribe
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError({'detail': 'Подписка не найдена.'})

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def list_subscriptions(self, request):
        subscriptions = Subscription.objects.filter(
            user=request.user).select_related('subscribed_to')

        subscribed_users = [sub.subscribed_to for sub in subscriptions]

        serializer = SubscriptionUserSerializer(
            subscribed_users,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': len(serializer.data),
            'results': serializer.data,
        })
