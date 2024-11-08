from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from users.models import Subscription
from .fields import Base64ImageField

User = get_user_model()


class UserSerializer(BaseUserSerializer):
    """
    Сериализатор для пользователя, расширяющий базовый сериализатор
    из Djoser. Добавляет поле аватара (с использованием base64) и
    информацию о подписке текущего пользователя на данного пользователя.
    """

    avatar = Base64ImageField(max_length=None, use_url=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar',)

    def update(self, instance, validated_data):
        avatar_data = validated_data.pop(
            'avatar', None)

        super().update(instance, validated_data)

        if avatar_data:
            instance.avatar = avatar_data
            instance.save()

        return instance

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user,
                                               subscribed_to=obj).exists()
        return False
