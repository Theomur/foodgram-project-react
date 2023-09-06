from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import permissions, serializers
from rest_framework.validators import UniqueValidator

from django.shortcuts import get_object_or_404

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            Subscribe, Tag)
from users.models import User


class CreateUserSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "username",
            "first_name",
            "last_name",
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        return (
            not user.is_anonymous
            and Subscribe.objects.filter(user=user, author=obj.id).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug", "color")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientsAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.pk")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class ShortRecipeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "name", "image", "cooking_time")


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsAmountSerializer(
        source="recipeingredient_set", many=True, read_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False
    )

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "author",
            "tags",
            "text",
            "image",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "cooking_time",
        )
        permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def validate(self, data):
        data["author"] = self.context["request"].user
        tags = self.initial_data.get("tags")
        if not isinstance(tags, list):
            raise serializers.ValidationError("теги не являются списком")
        if not Tag.objects.filter(id__in=tags).count() == len(tags):
            raise serializers.ValidationError("тегов нет")
        data["tags"] = tags
        ingredients = self.initial_data.get("ingredients")
        if not isinstance(ingredients, list):
            raise serializers.ValidationError(
                "ингредиенты не являются списком"
            )
        ingredients_valid = []
        for ingredient in ingredients:
            ingredient_object = get_object_or_404(
                Ingredient, id=ingredient.get("id")
            )
            amount = int(ingredient.get("amount"))

            if not isinstance(amount, int) or amount < 1:
                raise serializers.ValidationError("недопустимое количество")

            ingredients_valid.append(
                {"ingredient": ingredient_object, "amount": amount}
            )
        data["ingredients"] = ingredients_valid
        return data

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient["ingredient"],
                amount=ingredient["amount"],
            )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.get("tags")
        ingredients = validated_data.get("ingredients")

        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.image = validated_data.get("image", instance.image)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )

        if tags:
            instance.tags.clear()
            instance.tags.set(tags)

        if ingredients:
            instance.ingredients.clear()
            for ingredient in ingredients:
                RecipeIngredient.objects.get_or_create(
                    recipe=instance,
                    ingredient=ingredient["ingredient"],
                    amount=ingredient["amount"],
                )

        instance.save()
        return instance


class SubscribeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    username = serializers.ReadOnlyField(source="author.username")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "username",
            "recipes",
            "is_subscribed",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        is_subscribed = self.context.get("is_subscribed")
        if is_subscribed is None:
            return obj.is_subscribed
        return is_subscribed

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.author)
        limit = self.context.get("request").GET.get("recipes_limit")
        if limit:
            recipes = recipes[: int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        recipes_count = self.context.get("recipes_count")
        if recipes_count is None:
            return obj.recipes_count
        return recipes_count
