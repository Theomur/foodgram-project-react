from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            Shopping_cart, Tag)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from users.models import Subscribe, User

from .filters import RecipeFilter
from .pagination import PageSizeControlPagination
from .permissions import IsAuthentificatedAndAuthorOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeReadSerializer,
                          ShoppingSerializer, SubscribeSerializer,
                          SubscriptionsSerializer, TagSerializer)


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = PageSizeControlPagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated, ]
        return super(UserViewSet, self).get_permissions()

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,),
            pagination_class=PageSizeControlPagination)
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribed__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(page, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        if request.method == 'POST':
            data = {'user': user.id, 'author': author.id}
            serializer = SubscribeSerializer(data=data,
                                             context={"request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            instance = SubscriptionsSerializer(
                author,
                context={"request": request}
            )
            return Response(instance.data,
                            status=status.HTTP_201_CREATED)
        subscribe = Subscribe.objects.filter(user=user, author=author)
        deleted, _ = subscribe.delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response("Такой подписки нет",
                        status=status.HTTP_400_BAD_REQUEST)


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('^name', )


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    permission_classes = (AllowAny, )
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = PageSizeControlPagination
    permission_classes = (IsAuthentificatedAndAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    @staticmethod
    def create_object(serializer_class, pk, request):
        data = {'user': request.user.id, 'recipe': pk}
        serializer = serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def create_file_and_response(self, ingredients):
        file_list = []
        [file_list.append(
            '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
        file_content = 'Cписок покупок:\n' + '\n'.join(file_list)
        response = HttpResponse(file_content, content_type='text/plain')
        response['Content-Disposition'] = (
            f'attachment; filename={settings.FILE_NAME}'
        )
        return response

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            IngredientInRecipe.objects
            .filter(recipe__shopping_cart__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
            .values_list('ingredient__name', 'total_amount',
                         'ingredient__measurement_unit')
        )
        return self.create_file_and_response(ingredients)


class ShoppingListViewSet(DestroyModelMixin, CreateModelMixin, GenericViewSet):
    queryset = Shopping_cart.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ShoppingSerializer

    def create(self, request, *args, **kwargs):
        data = {'user': request.user.id, 'recipe': self.kwargs.get('id')}
        serializer = ShoppingSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        obj = Shopping_cart.objects.filter(
            user_id=request.user.id,
            recipe_id=self.kwargs.get('id')
        )
        if obj:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response("Такого рецепта нет в корзине",
                        status=status.HTTP_400_BAD_REQUEST)


class FavoriteListViewSet(DestroyModelMixin, CreateModelMixin, GenericViewSet):
    queryset = Favorite.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = FavoriteSerializer

    def create(self, request, *args, **kwargs):
        data = {'user': request.user.id, 'recipe': self.kwargs.get('id')}
        serializer = FavoriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        obj = Favorite.objects.filter(
            user_id=request.user.id,
            recipe_id=self.kwargs.get('id')
        )
        if obj:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response("Такого рецепта нет в избранном",
                        status=status.HTTP_400_BAD_REQUEST)
