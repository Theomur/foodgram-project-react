from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import permissions, serializers
from rest_framework.validators import UniqueValidator

from django.shortcuts import get_object_or_404

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            Subscription, Tag)
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
            "email",
            "id",
            "password",
            "username",
            "first_name",
            "last_name",
        )
        REQUIRED_FIELDS = (
            "email",
            "password",
            "username",
            "first_name",
            "last_name",
        )


class UserSerializer(UserSerializer):
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
            and Subscription.objects.filter(user=user, author=obj.id).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug", "color")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "measurement_unit")
        model = Ingredient


class IngredientsAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.pk")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        fields = ("id", "name", "measurement_unit", "amount")
        model = RecipeIngredient


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False
    )
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientsAmountSerializer(
        source="recipeingredient_set", many=True, read_only=True
    )
    image = Base64ImageField()

    class Meta:
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        model = Recipe
        permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def validate(self, data):
        data["author"] = self.context["request"].user
        tags = self.initial_data.get("tags")
        if not isinstance(tags, list):
            raise serializers.ValidationError("tags must be list")
        for tag in tags:
            if not Tag.objects.filter(id=tag).exists():
                raise serializers.ValidationError("No tag")
        data["tags"] = tags
        ingredients = self.initial_data.get("ingredients")
        if not isinstance(ingredients, list):
            raise serializers.ValidationError("ingredients must be list")
        valid_ingredients = []
        for ingredient in ingredients:
            ingredient_object = get_object_or_404(
                Ingredient, id=ingredient.get("id")
            )
            amount = int(ingredient.get("amount"))
            if not isinstance(amount, int) or amount < 1:
                raise serializers.ValidationError("invalid amount")
            valid_ingredients.append(
                {"ingredient": ingredient_object, "amount": amount}
            )
        data["ingredients"] = valid_ingredients
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
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
        ingredients = validated_data.get("ingredients")
        tags = validated_data.get("tags")

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


class RecipeShortSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionsSerializer(serializers.ModelSerializer):
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
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        is_subscribed = self.context.get("is_subscribed")
        if is_subscribed is None:
            return obj.is_subscribed
        return is_subscribed

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        recipes = Recipe.objects.all()
        if limit is not None:
            recipes = recipes[: int(limit)]
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        recipes_count = self.context.get("recipes_count")
        if recipes_count is None:
            return obj.recipes_count
        return recipes_count
