from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'text', 'cooking_time',
                    'get_ingredients', 'get_tags', 'author',)
    search_fields = ('name',)

    def get_ingredients(self, obj):
        return ", ".join(
            [f"{ri.name}" for ri in obj.ingredients.all()]
        )
    get_ingredients.short_description = 'Ингредиенты'

    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = 'Теги'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'amount',)
