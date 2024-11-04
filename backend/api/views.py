from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .decorators import relationship_action_decorator
from .filters import IngredientFilter, RecipeFilter
from .pagination import CommonPagination
from .permissions import IsAuthenticated, IsAuthenticatedOrOwnerOrReadOnly
from .serializers import (AddToListSerializer, IngredientSerializer,
                          RecipeSerializer, TagSerializer)


class IngredientViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer


class RecipeViewset(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-pub_date')
    permission_classes = [IsAuthenticatedOrOwnerOrReadOnly]
    serializer_class = RecipeSerializer
    pagination_class = CommonPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @relationship_action_decorator(url_path='favorite')
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self._toggle_recipe_relation(Favorite, request, recipe)

    @relationship_action_decorator(url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self._toggle_recipe_relation(ShoppingCart, request, recipe)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_items = ShoppingCart.objects.filter(user=user)

        ingredients_dict = {}

        for item in shopping_cart_items:
            recipe = item.recipe
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient_name = recipe_ingredient.ingredient.name
                meas_unit = recipe_ingredient.ingredient.measurement_unit
                amount = recipe_ingredient.amount

                if ingredient_name in ingredients_dict:
                    ingredients_dict[ingredient_name]['amount'] += amount
                else:
                    ingredients_dict[ingredient_name] = {
                        'amount': amount, 'unit': meas_unit}

        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"')

        for name, data in ingredients_dict.items():
            response.write(f'- {name} ({data["unit"]}) — {data["amount"]}\n')

        return response

    def _toggle_recipe_relation(self, model, request, recipe):
        user = request.user
        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=user, recipe=recipe)
            if created:
                serializer = AddToListSerializer(
                    recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            raise ValidationError({'detail': 'Рецепт уже добавлен.'})

        elif request.method == 'DELETE':
            deleted, _ = model.objects.filter(
                user=user, recipe=recipe).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError({'detail': 'Рецепт не найден в списке.'})
