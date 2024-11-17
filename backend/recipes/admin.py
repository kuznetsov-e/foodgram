from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from common.constants import ERROR_EMPTY_INGREDIENTS
from .models import Ingredient, Recipe, RecipeIngredient, Tag


class RecipeIngredientInlineFormSet(forms.BaseInlineFormSet):
    """
    Проверяет, что у рецепта есть хотя бы один ингредиент. Если все формы
    удалены или пусты, генерирует ошибку валидации.
    """

    def clean(self):
        super().clean()
        if not any(
                form.cleaned_data and not form.cleaned_data.get(
                    'DELETE', False)
                for form in self.forms):
            raise ValidationError(ERROR_EMPTY_INGREDIENTS)


class RecipeIngredientInline(admin.TabularInline):
    """
    Встраиваемая форма для отображения ингредиентов рецепта
    в интерфейсе администрирования.

    Это позволяет редактировать ингредиенты прямо на странице рецепта.
    """
    model = RecipeIngredient
    extra = 1
    formset = RecipeIngredientInlineFormSet


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'get_ingredients', 'get_tags',
                    'cooking_time', 'text', 'author', 'get_favorites_count',)
    search_fields = ('name', 'author__username',)
    list_filter = ('tags',)

    def get_ingredients(self, obj):
        return ', '.join(
            [f'{ri.name}' for ri in obj.ingredients.all()]
        )
    get_ingredients.short_description = 'Ингредиенты'

    def get_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = 'Теги'

    def get_favorites_count(self, obj):
        return obj.favorited_by.count()
    get_favorites_count.short_description = 'Количество добавлений в избранное'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
