from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator, RegexValidator
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers

from api.serializers import RecipeShortSerializer
from common.constants import REGEX, USERNAME_MAX_LENGTH
from common.fields import Base64ImageField
from common.serializers import UserSerializer

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    username = serializers.CharField(
        validators=[MaxLengthValidator(USERNAME_MAX_LENGTH), RegexValidator(
            regex=REGEX,
            message='Username must contain only letters, numbers, and .@+-',
            code='invalid_username'
        )])

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = User
        fields = ['avatar']


class SubscriptionUserSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        recipes_queryset = obj.recipes.all()
        if recipes_limit is not None and recipes_limit.isdigit():
            recipes_queryset = recipes_queryset[:int(recipes_limit)]

        return RecipeShortSerializer(recipes_queryset, many=True).data
