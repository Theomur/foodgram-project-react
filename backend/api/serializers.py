from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.transaction import atomic
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_base64.fields import Base64ImageField
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from users.models import Subscribe
from recipes.models import Favorite, Shopping_cart


User = get_user_model()


class SubscriptionMixin:
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Subscribe.objects.filter(user=request.user,
                                         author=obj).exists()
        )


class UsersSerializer(SubscriptionMixin, UserSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed')


class RecipeShortSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name',
                  'image', 'cooking_time')


class SubscriptionsSerializer(UsersSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UsersSerializer.Meta.fields + (
            'recipes_count', 'recipes'
        )
        read_only_fields = ('email', 'username')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeShortSerializer(recipes,
                                           many=True,
                                           read_only=True)
        return serializer.data


class SubscribeSerializer(serializers.Serializer):
    class Meta:
        model = Subscribe
        fields = ('user', 'author')

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscribe.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name',
                  'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UsersSerializer()
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipes')
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and user.favorites.filter(recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and user.shopping_cart.filter(recipe=obj).exists())


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30000)]
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    author = UsersSerializer(read_only=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30000)]
    )

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients',
                  'tags', 'image',
                  'name', 'text',
                  'cooking_time', 'author')

    def validate(self, obj):
        if not obj.get('tags'):
            raise serializers.ValidationError(
                {'tags': 'Нужно указать минимум 1 тег.'}
            )
        if len({tag.id for tag in obj.get('tags')}) != len(obj.get('tags')):
            raise serializers.ValidationError(
                {'tags': 'Теги должны быть уникальны.'}
            )
        if not obj.get('ingredients'):
            raise serializers.ValidationError(
                {'ingredients': 'Нужно указать минимум 1 ингредиент.'}
            )
        if (len({ingredient['id'] for ingredient in obj.get('ingredients')})
           != len(obj.get('ingredients'))):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты должны быть уникальны.'}
            )
        return obj

    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        ingredient_objs = []
        for ingredient in ingredients:
            ingredient_objs.append(IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ))
        IngredientInRecipe.objects.bulk_create(ingredient_objs)

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance,
                                    context=self.context).data


class ShoppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shopping_cart
        fields = (
            'user',
            'recipe',
        )

    def validate(self, data):
        if Shopping_cart.objects.filter(
                user_id=data['user'],
                recipe_id=data['recipe']):
            raise serializers.ValidationError(
                {'shopping_cart': 'Рецепт уже в вашей корзине'})
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe).data


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = (
            'user',
            'recipe',
        )

    def validate(self, data):
        if Favorite.objects.filter(
                user_id=data['user'],
                recipe_id=data['recipe']):
            raise serializers.ValidationError(
                {'favorite': 'Рецепт уже в вашем избранном'})
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe).data
