from django.db import models
from users.models import User
from django.core.validators import MinValueValidator, RegexValidator
from foodgram.settings import LINE_LIMIT


class Tag(models.Model):
    name = models.CharField(
        LINE_LIMIT,
        unique=True
    )

    slug = models.SlugField(unique=True)

    color = models.CharField(
        'Цвет в HEX',
        max_length=7,
        null=True,
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Поле должно содержать HEX-код выбранного цвета.'
            )
        ]
    )

    class Meta:
        verbose_name = 'Тег'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(LINE_LIMIT)
    measurement_unit = models.CharField(LINE_LIMIT)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингридиент'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(LINE_LIMIT)
    text = models.TextField()
    image = models.ImageField(
        upload_to='recipes/',
        blank=False
    )
    cooking_time = models.IntegerField(validators=[MinValueValidator(1)])
    pub_date = models.DateTimeField(
        auto_now_add=True)
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='Ingredient_In_Recipe',
        through_fields=('recipe', 'ingredient'),)

    class Meta:
        ordering = ['-pub_date']
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

    amount = models.IntegerField(validators=[MinValueValidator(1)])

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
            f'{self.amount}')


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite'
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
