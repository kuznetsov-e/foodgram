from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator, RegexValidator
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers

from api.serializers import RecipeShortSerializer
from common.constants import (EMAIL_MAX_LENGTH, ERROR_INVALID_USERNAME,
                              NAME_MAX_LENGTH, REGEX)
from common.fields import Base64ImageField
from common.serializers import UserSerializer

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    username = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        validators=[RegexValidator(
            regex=REGEX,
            message=ERROR_INVALID_USERNAME
        )])
    email = serializers.EmailField(
        validators=[EmailValidator], max_length=EMAIL_MAX_LENGTH)
    first_name = serializers.CharField(max_length=NAME_MAX_LENGTH)
    last_name = serializers.CharField(max_length=NAME_MAX_LENGTH)

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')


class UserAvatarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для загрузки и получения аватарок пользователей,
    поддерживающий формат base64 для передачи изображений.
    """

    avatar = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = User
        fields = ['avatar']


class SubscriptionUserSerializer(UserSerializer):
    """
    Сериализатор для подписок пользователя, включает их рецепты с
    возможностью ограничения по количеству через параметр запроса,
    а также общее количество рецептов.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """
        Получает список рецептов для подписанного пользователя
        с возможным ограничением по количеству.

        Аргументы:
            obj: Объект пользователя.

        Возвращает:
            Список сериализованных рецептов пользователя, с ограничением,
            если указано.
        """
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        recipes_queryset = obj.recipes.all()
        if recipes_limit is not None and recipes_limit.isdigit():
            recipes_queryset = recipes_queryset[:int(recipes_limit)]

        return RecipeShortSerializer(recipes_queryset, many=True).data
