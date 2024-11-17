import uuid

from django.contrib.auth import get_user_model
from django.db import models

from common.constants import (DEFAULT_MAX_LENGTH, RECIPE_IMAGE_UPLOAD_FOLDER,
                              RECIPE_NAME_MAX_LENGTH, SHORT_CODE_MAX_LENGTH)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=False, null=False,
        verbose_name='Название')
    slug = models.SlugField(
        blank=False, null=False,
        verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=False, null=False,
        verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=False, null=False,
        verbose_name='Единица измерения')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'], name='unique_ingredient')
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        blank=False, null=False,
        verbose_name='Название')
    image = models.ImageField(
        blank=False, null=False,
        upload_to=RECIPE_IMAGE_UPLOAD_FOLDER,
        verbose_name='Фото')
    text = models.TextField(
        blank=False, null=False,
        verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        blank=False, null=False,
        verbose_name='Время приготовления (минут)')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Список ингредиентов')
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Список тегов')
    author = models.ForeignKey(
        User,
        blank=False, null=False,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации')
    short_code = models.CharField(
        max_length=SHORT_CODE_MAX_LENGTH,
        unique=True, blank=True,
        verbose_name='Код для короткой ссылки')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Переопределённый метод save для генерации short_code перед сохранением.
        Если short_code отсутствует, генерируется на основе обрезанного UUID.
        """
        if not self.short_code:
            self.short_code = str(uuid.uuid4())[:SHORT_CODE_MAX_LENGTH]
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    """
    Модель для связи рецептов и ингредиентов.
    Каждый рецепт может содержать несколько ингредиентов
    с определённым количеством.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиенты')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество')

    class Meta:
        default_related_name = 'recipe_ingredients'
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return f'{self.ingredient.name} (' \
            f'{self.amount} {self.ingredient.measurement_unit})'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite')
        ]

    def __str__(self):
        return f'Избранное: {self.user.username} -> {self.recipe.name}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_carts')

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart')
        ]

    def __str__(self):
        return f'Корзина: {self.user.username} -> {self.recipe.name}'
