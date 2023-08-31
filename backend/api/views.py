from django.db.models import BooleanField, Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Favorite, Ingredient, Ingredient_In_Recipe, Recipe,
                            Shopping_cart, Tag)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscribe, User
from foodgram.settings import FILE_NAME

from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomPageNumberPagination, IngredientSerializer,
                          ReadUsersSerializer, RecipeCreateSerializer,
                          RecipeReadSerializer, RecipeShortSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserCreateSerializer)

favorite_subquery = Favorite.objects.filter(user=OuterRef('pk'),
                                            recipe=OuterRef('pk'))
shopping_cart_subquery = Shopping_cart.objects.filter(user=OuterRef('pk'),
                                                      recipe=OuterRef('pk'))


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPageNumberPagination
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReadUsersSerializer
        return UserCreateSerializer

    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = ReadUsersSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(pages, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            Subscribe.objects.create(user=request.user, author=author)
            return Response(status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            try:
                subscription = Subscribe.objects.get(
                    user=request.user, author=author)
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Subscribe.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)


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
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def get_queryset(self):
        queryset = Recipe.objects.annotate(
            is_favorited=Exists(favorite_subquery,
                                output_field=BooleanField()),
            is_in_shopping_cart=Exists(shopping_cart_subquery,
                                       output_field=BooleanField()),
        )
        return queryset

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = RecipeShortSerializer(recipe, data=request.data,
                                               context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not Favorite.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                Favorite.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(
                    user=request.user, recipe=recipe)
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Favorite.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = RecipeShortSerializer(recipe, data=request.data,
                                               context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not Shopping_cart.objects.filter(user=request.user,
                                                recipe=recipe).exists():
                Shopping_cart.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(Shopping_cart, user=request.user,
                              recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            Ingredient_In_Recipe.objects
            .filter(recipe__shopping_recipe__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
            .values_list('ingredient__name', 'total_amount',
                         'ingredient__measurement_unit')
        )
        file_list = []
        [file_list.append(
            '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
        file = HttpResponse('Cписок покупок:\n' + '\n'.join(file_list),
                            content_type='text/plain')
        file['Content-Disposition'] = (f'attachment; filename={FILE_NAME}')
        return file
