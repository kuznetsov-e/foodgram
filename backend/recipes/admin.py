from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag


class RecipeIngredientInline(admin.TabularInline):
    """
    Встраиваемая форма для отображения ингредиентов рецепта
    в интерфейсе администрирования.

    Это позволяет редактировать ингредиенты прямо на странице рецепта.
    """
    model = RecipeIngredient
    extra = 1


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
