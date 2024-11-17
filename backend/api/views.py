from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.constants import (ERROR_ALREADY_SUBSCRIBED,
                              ERROR_CANNOT_SUBSCRIBE_TO_SELF, ERROR_CART_EMPTY,
                              ERROR_RECIPE_ALREADY_ADDED,
                              ERROR_RECIPE_NOT_FOUND,
                              ERROR_SUBSCRIPTION_NOT_FOUND, RECIPES_URL_PATH,
                              SHOPPING_CART_FILENAME, SHORT_URL_PATH,
                              URL_AVATAR_PATH, URL_CURRENT_USER_PATH,
                              URL_DOWNLOAD_SHOPPING_CART_PATH,
                              URL_FAVORITES_PATH, URL_GET_LINK_PATH,
                              URL_SHOPPING_CART_PATH, URL_SUBSCRIBE_PATH,
                              URL_SUBSCRIPTIONS_PATH)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription
from .decorators import relationship_action_decorator
from .filters import IngredientFilter, RecipeFilter
from .pagination import CommonPagination
from .permissions import IsAuthenticated, IsAuthenticatedOrOwnerOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeReadSerializer, RecipeShortSerializer,
                          SubscriptionUserSerializer, TagSerializer,
                          UserAvatarSerializer, UserSerializer)

User = get_user_model()


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

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrOwnerOrReadOnly]
    pagination_class = CommonPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Recipe.objects.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk'))
                )
            )
        return Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        """Назначает текущего пользователя автором рецепта при создании."""
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        recipe = serializer.instance
        read_serializer = RecipeReadSerializer(
            recipe, context={'request': request})

        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        updated_recipe = serializer.instance
        read_serializer = RecipeReadSerializer(
            updated_recipe, context={'request': request})

        return Response(read_serializer.data, status=status.HTTP_200_OK)

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
        ingredients = (
            ShoppingCart.objects
            .filter(user=user)
            .select_related('recipe')
            .prefetch_related(
                'recipe__recipe_ingredients__ingredient')
            .values(
                'recipe__recipe_ingredients__ingredient__name',
                'recipe__recipe_ingredients__ingredient__measurement_unit')
            .annotate(total_amount=Sum('recipe__recipe_ingredients__amount'))
            .order_by('recipe__recipe_ingredients__ingredient__name'))

        if not ingredients:
            return Response(
                {'detail': ERROR_CART_EMPTY},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            f'attachment; filename="{SHOPPING_CART_FILENAME}"')

        for ingredient in ingredients:
            ingredient_name = ingredient[
                'recipe__recipe_ingredients__ingredient__name']
            meas_unit = ingredient[
                'recipe__recipe_ingredients__ingredient__measurement_unit']
            total_amount = ingredient['total_amount']

            response.write(
                f'- {ingredient_name} ({meas_unit}) — {total_amount}\n')

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


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CommonPagination

    @action(detail=False, methods=['get'], url_path=URL_CURRENT_USER_PATH,
            permission_classes=[IsAuthenticated])
    def me(self, request):
        """Возвращает данные текущего авторизованного пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path=URL_AVATAR_PATH,
            permission_classes=[IsAuthenticated])
    def update_avatar(self, request):
        """Обновляет или удаляет аватар пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user, data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
            self.perform_update(serializer)
            return Response(serializer.data)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated], url_path=URL_SUBSCRIBE_PATH)
    def subscribe(self, request, id=None):
        """Осуществляет подписку на или отписку от другого пользователя."""
        user = request.user
        if user.id == int(id):
            return Response({'detail': ERROR_CANNOT_SUBSCRIBE_TO_SELF},
                            status=status.HTTP_400_BAD_REQUEST)

        user_to_subscribe = get_object_or_404(User, id=id)

        if request.method == 'POST':
            _, created = Subscription.objects.get_or_create(
                user=user, subscribed_to=user_to_subscribe
            )
            if created:
                serializer = SubscriptionUserSerializer(
                    user_to_subscribe, context={'request': request})
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                {'detail': ERROR_ALREADY_SUBSCRIBED},
                status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=user, subscribed_to=user_to_subscribe
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': ERROR_SUBSCRIPTION_NOT_FOUND},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=URL_SUBSCRIPTIONS_PATH)
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
        subscribed_users = User.objects.filter(
            subscribers__user=request.user
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(subscribed_users, request)

        serializer = SubscriptionUserSerializer(
            page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


def short_link_redirect(request, short_code):
    """Перенаправляет на страницу рецепта по его короткому коду."""
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return redirect(f'/{RECIPES_URL_PATH}/{recipe.id}')
