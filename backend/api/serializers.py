from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator, RegexValidator
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer)
from rest_framework import serializers

from common.constants import (ABOVE_ZERO_VALUE, EMAIL_MAX_LENGTH,
                              ERROR_DUPLICATE_INGREDIENTS,
                              ERROR_DUPLICATE_TAGS, ERROR_EMPTY_INGREDIENTS,
                              ERROR_EMPTY_TAGS, ERROR_INVALID_USERNAME,
                              ERROR_RECIPES_LIMIT_NOT_DIGIT, NAME_MAX_LENGTH,
                              REGEX)
from common.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

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
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(
                subscribed_to=obj
            ).exists()
        )


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
                  'first_name', 'last_name', 'password',)


class UserAvatarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для загрузки и получения аватарок пользователей,
    поддерживающий формат base64 для передачи изображений.
    """

    avatar = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = User
        fields = ('avatar',)


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
        if recipes_limit is not None:
            if recipes_limit.isdigit():
                recipes_queryset = recipes_queryset[:int(recipes_limit)]
            else:
                raise serializers.ValidationError(
                    ERROR_RECIPES_LIMIT_NOT_DIGIT
                )

        return RecipeShortSerializer(recipes_queryset, many=True).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов с количеством в рецепте."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeIngredientInputSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ввода ингредиентов (через id)
    с количеством при создании рецепта.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=ABOVE_ZERO_VALUE)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    image = Base64ImageField(use_url=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientAmountSerializer(
        source='recipe_ingredients', many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'text', 'cooking_time', 'ingredients',
                  'tags', 'author', 'is_favorited', 'is_in_shopping_cart',)

    def get_is_favorited(self, obj):
        return self._check_recipe_relation(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self._check_recipe_relation(ShoppingCart, obj)

    def _check_recipe_relation(self, model, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return model.objects.filter(user=request.user, recipe=obj).exists()
        return False


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    image = Base64ImageField(use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientInputSerializer(
        many=True, source='recipe_ingredients')
    cooking_time = serializers.IntegerField(min_value=ABOVE_ZERO_VALUE)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'text', 'cooking_time',
                  'ingredients', 'tags', 'author',)

    def validate(self, data):
        """
        Проверяет наличие полей 'ингредиенты' и 'теги',
        их заполнение и уникальность.
        """
        required_fields = {
            'recipe_ingredients': ERROR_EMPTY_INGREDIENTS,
            'tags': ERROR_EMPTY_TAGS,
        }

        for field, error_message in required_fields.items():
            if field not in data or not data[field]:
                raise serializers.ValidationError({field: error_message})

        seen_ids = set()
        for ingredient in data['recipe_ingredients']:
            ingredient_id = ingredient['id']
            if ingredient_id in seen_ids:
                raise serializers.ValidationError(
                    {'recipe_ingredients': ERROR_DUPLICATE_INGREDIENTS})
            seen_ids.add(ingredient_id)

        if len(data['tags']) != len(set(data['tags'])):
            raise serializers.ValidationError({'tags': ERROR_DUPLICATE_TAGS})

        return data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        self._set_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredients')

        instance = super().update(instance, validated_data)

        instance.tags.set(tags_data)

        self._set_ingredients(instance, ingredients_data)
        return instance

    def _set_ingredients(self, recipe, ingredients_data):
        """
        Вспомогательный метод для массового создания объектов RecipeIngredient.
        """
        recipe.recipe_ingredients.all().delete()

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]

        RecipeIngredient.objects.bulk_create(recipe_ingredients)


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Краткий сериализатор для модели рецепта, включающий только основные поля.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
