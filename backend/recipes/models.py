from django.conf import settings
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=settings.LINE_LIMIT_RECIPES,
        unique=True,
        verbose_name='название'
    )

    slug = models.SlugField(
        max_length=settings.LINE_LIMIT_RECIPES,
        unique=True,
        verbose_name='уникальный слаг'
    )

    color = models.CharField(
        max_length=7,
        null=True,
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Поле должно содержать HEX-код выбранного цвета.'
            )
        ],
        verbose_name='цвет'
    )

    class Meta:
        verbose_name = 'Тег'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(max_length=settings.LINE_LIMIT_RECIPES,
                            verbose_name='название')
    measurement_unit = models.CharField(max_length=settings.LINE_LIMIT_RECIPES,
                                        verbose_name='еденица измерения')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit'
            )
        ]

        ordering = ('name',)
        verbose_name = 'Ингридиент'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='автор'
    )
    name = models.CharField(max_length=settings.LINE_LIMIT_RECIPES,
                            verbose_name='название')
    text = models.TextField(verbose_name='описание')
    image = models.ImageField(
        upload_to='recipes/',
        blank=False,
        verbose_name='картинка'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1),
                    MaxValueValidator(30000)],
        verbose_name='время готовки'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='ыремя публикации')
    tags = models.ManyToManyField(Tag, verbose_name='теги')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        through_fields=('recipe', 'ingredient'),
        verbose_name='ингредиенты'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент'
    )

    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1),
                    MaxValueValidator(30000)]
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_combination'
            )
        ]

    def __str__(self):
        return (
            f'"{self.ingredient.name}" в "{self.recipe.name}": '
            f'{self.amount}')


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Shopping_cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='рецепт'
    )

    class Meta:
        verbose_name = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
