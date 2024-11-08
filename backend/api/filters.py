from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
import django_filters

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart

User = get_user_model()


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов по тегам, избранному, корзине и автору."""

    tags = django_filters.CharFilter(method='filter_by_tags')
    is_favorited = django_filters.CharFilter(method='filter_by_favorites')
    is_in_shopping_cart = django_filters.CharFilter(
        method='filter_by_shopping_cart')
    author = django_filters.NumberFilter(
        field_name='author_id', lookup_expr='exact')

    class Meta:
        model = Recipe
        fields = ['tags', 'is_favorited', 'is_in_shopping_cart', 'author']

    def filter_by_favorites(self, queryset, name, value):
        """Фильтрует рецепты, добавленные в избранное текущим пользователем."""
        return self._filter_by_relation(queryset, name, value, Favorite,
                                        'recipe')

    def filter_by_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты, добавленные в корзину текущим пользователем."""
        return self._filter_by_relation(queryset, name, value, ShoppingCart,
                                        'recipe')

    def filter_by_tags(self, queryset, name, value):
        """Фильтрует рецепты по указанным тегам."""
        tag_list = self.request.query_params.getlist('tags')

        if not tag_list:
            return queryset
        return queryset.filter(tags__slug__in=tag_list).distinct()

    def _filter_by_relation(
            self, queryset, name, value, model, relation_field):
        """Вспомогательный метод для фильтрации по связанным объектам
        (избранное или корзина) для текущего пользователя.
        """
        user = self.request.user

        if value == '1' and user.is_authenticated:
            return queryset.annotate(
                is_related=Exists(model.objects.filter(
                    user=user, **{relation_field: OuterRef('pk')})
                )
            ).filter(is_related=True)
        elif value == '0' and user.is_authenticated:
            return queryset.annotate(
                is_related=Exists(model.objects.filter(
                    user=user, **{relation_field: OuterRef('pk')})
                )
            ).filter(is_related=False)

        return queryset


class IngredientFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов по имени, начиная с введённого текста."""
    name = django_filters.CharFilter(
        field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_queryset(self, queryset):
        """
        Фильтрует ингредиенты по имени, используя переданный параметр name.
        """
        decoded_name = unquote(self.data.get('name', ''))
        return queryset.filter(name__istartswith=decoded_name)
