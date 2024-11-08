from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response

from common.constants import (ERROR_CART_EMPTY, ERROR_NOT_AUTHENTICATED,
                              ERROR_RECIPE_ALREADY_ADDED,
                              ERROR_RECIPE_NOT_FOUND, RECIPES_URL_PATH,
                              SHOPPING_CART_FILENAME, SHORT_URL_PATH,
                              URL_DOWNLOAD_SHOPPING_CART_PATH,
                              URL_FAVORITES_PATH, URL_GET_LINK_PATH,
                              URL_SHOPPING_CART_PATH)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .decorators import relationship_action_decorator
from .filters import IngredientFilter, RecipeFilter
from .pagination import CommonPagination
from .permissions import IsAuthenticated, IsAuthenticatedOrOwnerOrReadOnly
from .serializers import (IngredientSerializer, RecipeSerializer,
                          RecipeShortSerializer, TagSerializer)


class IngredientViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer


class RecipeViewset(viewsets.ModelViewSet):
    """
    Вьюсет для управления рецептами. Включает действия по добавлению/удалению
    рецептов в избранное и корзину покупок, создание короткой ссылки
    и загрузку списка покупок в виде файла формата ".txt".
    """

    queryset = Recipe.objects.all().order_by('-pub_date')
    permission_classes = [IsAuthenticatedOrOwnerOrReadOnly]
    serializer_class = RecipeSerializer
    pagination_class = CommonPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        """Назначает текущего пользователя автором рецепта при создании."""
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed(ERROR_NOT_AUTHENTICATED)
        serializer.save(author=self.request.user)

    @relationship_action_decorator(url_path=URL_FAVORITES_PATH)
    def favorite(self, request, pk=None):
        """
        Добавляет или удаляет указанный рецепт из избранного пользователя.
        """
        recipe = self.get_object()
        return self._toggle_recipe_relation(Favorite, request, recipe)

    @relationship_action_decorator(url_path=URL_SHOPPING_CART_PATH)
    def shopping_cart(self, request, pk=None):
        """
        Добавляет или удаляет указанный рецепт из корзины покупок пользователя.
        """
        recipe = self.get_object()
        return self._toggle_recipe_relation(ShoppingCart, request, recipe)

    @action(detail=True, methods=['get'], url_path=URL_GET_LINK_PATH,
            permission_classes=[permissions.AllowAny])
    def get_link(self, request, pk=None):
        """Генерирует короткую ссылку для указанного рецепта."""
        recipe = self.get_object()
        base_url = request.build_absolute_uri('/')[:-1]
        short_link = f'{base_url}/{SHORT_URL_PATH}/{recipe.short_code}'
        return Response({'short-link': short_link})

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path=URL_DOWNLOAD_SHOPPING_CART_PATH)
    def download_shopping_cart(self, request):
        """
        Генерирует и загружает текстовый файл со списком ингредиентов
        для всех рецептов в корзине покупок пользователя.
        """
        user = request.user
        shopping_cart_items = ShoppingCart.objects.filter(user=user)

        if not shopping_cart_items.exists():
            return Response(
                {'detail': ERROR_CART_EMPTY},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            f'attachment; filename="{SHOPPING_CART_FILENAME}"')

        for name, data in ingredients_dict.items():
            response.write(f'- {name} ({data["unit"]}) — {data["amount"]}\n')

        return response

    def _toggle_recipe_relation(self, model, request, recipe):
        """
        Вспомогательный метод для добавления или удаления связи рецепта,
        например, добавление/удаление рецепта из избранного или корзины.
        """
        user = request.user
        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=user, recipe=recipe)
            if created:
                serializer = RecipeShortSerializer(
                    recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            raise ValidationError({'detail': ERROR_RECIPE_ALREADY_ADDED})

        elif request.method == 'DELETE':
            deleted, _ = model.objects.filter(
                user=user, recipe=recipe).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError({'detail': ERROR_RECIPE_NOT_FOUND})


def short_link_redirect(request, short_code):
    """Перенаправляет на страницу рецепта по его короткому коду."""
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return redirect(f'/{RECIPES_URL_PATH}/{recipe.id}')
