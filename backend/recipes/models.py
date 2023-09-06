from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=settings.LENGTH_OF_FIELDS_RECIPES_RELATED, unique=True
    )
    slug = models.SlugField(
        max_length=settings.LENGTH_OF_FIELDS_RECIPES_RELATED, unique=True
    )
    color = models.CharField(max_length=7, unique=True)

    class Meta:
        verbose_name = "Тег"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=settings.LENGTH_OF_FIELDS_RECIPES_RELATED
    )
    measurement_unit = models.CharField(
        max_length=settings.LENGTH_OF_FIELDS_RECIPES_RELATED
    )

    class Meta:
        unique_together = ("name", "measurement_unit")
        verbose_name = "Ингредиент"

    def str(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipe",
    )
    name = models.CharField(
        max_length=settings.LENGTH_OF_FIELDS_RECIPES_RELATED
    )
    text = models.TextField()
    image = models.ImageField(upload_to="recipes/", blank=False)
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время готовки",
        validators=[
            MinValueValidator(
                1, message="Время приготовления не менее 1 минуты!"
            ),
            MaxValueValidator(
                1441, message="Время приготовления не более 24 часов!"
            ),
        ],
    )
    tags = models.ManyToManyField(Tag, related_name="tags")
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name="recipe_ingredients",
        through="recipes.RecipeIngredient",
    )

    class Meta:
        verbose_name = "Рецепт"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество",
    )

    def str(self):
        return self.ingredient

    class Meta:
        verbose_name = "Ингредиенты в рецепте"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_combination"
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        related_name="favorite"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorite",
        blank=True
    )

    class Meta:
        verbose_name = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriber",
        blank=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribed",
        blank=True,
    )

    class Meta:
        verbose_name = "Подписка на авторов"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "author"), name="unique_subscribe"
            )
        ]


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
    )

    class Meta:
        verbose_name = "Корзина"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_list"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
