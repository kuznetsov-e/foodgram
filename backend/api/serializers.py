from rest_framework import serializers

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
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeIngredientInputSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientInputSerializer(
        many=True, source='recipe_ingredients')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'cooking_time',
            'ingredients',
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True).data
        representation['ingredients'] = IngredientAmountSerializer(
            instance.recipe_ingredients.all(), many=True).data
        return representation

    def create(self, validated_data):
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

    def get_is_favorited(self, obj):
        return self._check_recipe_relation(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self._check_recipe_relation(ShoppingCart, obj)

    def _check_recipe_relation(self, model, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return model.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_image(self, obj):
        from users.fields import Base64ImageField
        return Base64ImageField().to_representation(obj.image)

    def get_author(self, obj):
        from users.serializers import UserSerializer
        return UserSerializer(obj.author, context=self.context).data


class AddToListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
