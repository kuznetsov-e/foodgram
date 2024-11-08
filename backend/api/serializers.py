from rest_framework import serializers

from common.constants import (ERROR_DUPLICATE_INGREDIENTS,
                              ERROR_DUPLICATE_TAGS, ERROR_EMPTY_INGREDIENTS,
                              ERROR_EMPTY_TAGS,
                              ERROR_MISSING_INGREDIENTS_FIELD,
                              ERROR_MISSING_TAGS_FIELD)
from common.fields import Base64ImageField
from common.serializers import UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов с количеством в рецепте."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeIngredientInputSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ввода ингредиентов (через id)
    с количеством при создании рецепта.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    image = Base64ImageField(max_length=None, use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True)
    ingredients = RecipeIngredientInputSerializer(
        many=True, source='recipe_ingredients', required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'text', 'cooking_time', 'ingredients',
                  'tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное текущего пользователя."""
        return self._check_recipe_relation(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину текущего пользователя."""
        return self._check_recipe_relation(ShoppingCart, obj)

    def validate_ingredients(self, value):
        """
        Проверяет наличие ингредиентов
        и отсутствие дублирующихся ингредиентов в рецепте.
        """
        if not value:
            raise serializers.ValidationError(ERROR_EMPTY_INGREDIENTS)

        seen_ids = set()
        for ingredient in value:
            ingredient_id = ingredient['id']
            if ingredient_id in seen_ids:
                raise serializers.ValidationError(ERROR_DUPLICATE_INGREDIENTS)
            seen_ids.add(ingredient_id)

        return value

    def validate_tags(self, value):
        """
        Проверяет наличие тегов и отсутствие дублирующихся тегов в рецепте.
        """
        if not value:
            raise serializers.ValidationError(ERROR_EMPTY_TAGS)

        unique_tags = set(value)
        if len(unique_tags) != len(value):
            raise serializers.ValidationError(ERROR_DUPLICATE_TAGS)

        return value

    def validate(self, data):
        """
        Проверяет наличие полей 'ингредиенты' и 'теги'
        при обновлении рецепта.
        """
        if self.context['request'].method == 'PATCH':
            if 'recipe_ingredients' not in data:
                raise serializers.ValidationError(
                    ERROR_MISSING_INGREDIENTS_FIELD)
            if 'tags' not in data:
                raise serializers.ValidationError(
                    ERROR_MISSING_TAGS_FIELD)

        return data

    def to_representation(self, instance):
        """
        Формирует представление рецепта
        с вложенными сериализаторами для тегов и ингредиентов.
        """
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True).data
        representation['ingredients'] = IngredientAmountSerializer(
            instance.recipe_ingredients.all(), many=True).data
        return representation

    def create(self, validated_data):
        """
        Создаёт экземпляр рецепта с заданными тегами и ингредиентами,
        используя промежуточную модель RecipeIngredient для связи
        рецепта с ингредиентами и их количеством.
        """
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт и пересоздает список ингредиентов и тегов."""
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.save()

        tags_data = validated_data.get('tags')
        if tags_data is not None:
            instance.tags.set(tags_data)

        ingredients_data = validated_data.get('recipe_ingredients')
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )

        return instance

    def _check_recipe_relation(self, model, obj):
        """
        Вспомогательный меотодя для проверки наличия связи рецепта
        с текущим пользователем для указанной модели.
        """
        request = self.context.get('request')
        if request.user.is_authenticated:
            return model.objects.filter(user=request.user, recipe=obj).exists()
        return False


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Краткий сериализатор для модели рецепта, включающий только основные поля.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
