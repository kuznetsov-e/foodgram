import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=32)
    slug = models.SlugField(max_length=32, null=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipe_images/')
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField()
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient')
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')
    pub_date = models.DateTimeField(auto_now_add=True)
    short_code = models.CharField(max_length=10, unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = str(uuid.uuid4())[:5]
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-pub_date']


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='ingredient_recipes')
    amount = models.PositiveSmallIntegerField()

    class Meta:
        default_related_name = 'recipe_ingredients'

    def __str__(self):
        return (f'{self.recipe} - {self.ingredient}, '
                f'{self.amount} {self.ingredient.measurement_unit}')


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="favorites")
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='in_shopping_carts')

    class Meta:
        unique_together = ('user', 'recipe')
