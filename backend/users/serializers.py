from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer)
from rest_framework import serializers

from api.serializers import RecipeSerializer
from recipes.models import Recipe
from .fields import Base64ImageField
from .models import Subscription

User = get_user_model()


class UserSerializer(BaseUserSerializer):
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


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')


class SubscriptionUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(max_length=None, use_url=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes',
                  'recipes_count', 'avatar',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user,
                                               subscribed_to=obj).exists()
        return False

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        return RecipeSerializer(recipes, many=True, context=self.context).data
