from django.db import models
from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200)

    slug = models.SlugField(
        unique=True,
        null=True
    )

    color = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Тег'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингридиент'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(
        upload_to='recipes/',
        blank=True
    )
    cooking_time = models.IntegerField()
    pub_date = models.DateTimeField(
        auto_now_add=True
        )
    tags = models.ManyToManyField(
        Tag
        )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='Ingredient_In_Recipe',
        through_fields=('recipe', 'ingredient'),
        )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'

    def __str__(self):
        return self.name


class Ingredient_In_Recipe(models.Model):
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

    amount = models.IntegerField()

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_combination'
            )
        ]

    def __str__(self):
        return (
            f'"{self.ingredient.name}" в "{self.recipe.name}": '
            f'{self.amount}, '
            f'{self.ingredient.measurement_unit}'
            )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_user'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe'
    )

    class Meta:
        verbose_name = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Shopping_cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_user',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_recipe',
    )

    class Meta:
        verbose_name = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
