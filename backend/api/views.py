from http import HTTPStatus
from io import BytesIO

from django.db import transaction
from django.db.models import BooleanField, Count, Exists, OuterRef, Sum, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingBasket, Tag)
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from users.models import Follow, User

from .filters import IngredientSearchFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly, IsAdminOrReadOnly
from .serializers import (AddingRecipesSerializer, CheckFollowSerializer,
                          CreateRecipeSerializer, FavoritesSerializer,
                          FollowSerializer, IngredientsSerializer,
                          ReadRecipesSerializer, ShoppingBasketsSerializer,
                          TagsSerializer)

FILE_NAME = 'shopping-list.txt'
TITLE_SHOP_LIST = 'Список покупок с сайта Foodgram:\n\n'


def generate_shopping_cart_content(self, ingredients):
    """Генерация содержимого файла листа покупок."""
    content = BytesIO()
    content.write(TITLE_SHOP_LIST.encode('utf-8'))
    content.write(
        "\n".join(
            [
                f'{ingredient["ingredient__name"]} - {ingredient["total"]}/'
                f'{ingredient["ingredient__measurement_unit"]}'
                for ingredient in ingredients
            ]
        ).encode('utf-8')
    )
    content.seek(0)
    return content


class ListRetrieveViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    permission_classes = (IsAdminOrReadOnly,)


class TagsViewSet(ListRetrieveViewSet):
    """Класс взаимодействия с моделью Tags. Вьюсет для списка тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class IngredientsViewSet(ListRetrieveViewSet):
    """Класс взаимодействия с моделью Ingredients. Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_class = IngredientSearchFilter


class RecipesViewSet(viewsets.ModelViewSet):
    """Класс взаимодействия с моделью Recipes. Вьюсет для рецептов."""

    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        """Сериализаторы для рецептов."""
        if self.request.method in SAFE_METHODS:
            return ReadRecipesSerializer
        return CreateRecipeSerializer

    def get_queryset(self):
        """Резюме по объектам с помощью annotate()."""
        if self.request.user.is_authenticated:
            return Recipe.objects.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user, recipe__pk=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingBasket.objects.filter(
                        user=self.request.user, recipe__pk=OuterRef('pk')
                    )
                ),
            )
        return Recipe.objects.annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField()),
        )

    @transaction.atomic()
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True, methods=['POST'], permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        """Добавить в избранное."""
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = FavoritesSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.add_object(Favorite, request.user, pk)

    @favorite.mapping.delete
    def del_favorite(self, request, pk=None):
        """Убрать из избранного."""
        favorite = Favorite.objects.filter(user=request.user, recipe=pk)
        if favorite.exists():
            favorite.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        else:
            return Response({'detail': 'Избранное не найдено.'},
                            status=HTTPStatus.NOT_FOUND)

    @action(
        detail=True, methods=['POST'], permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """Добавить в лист покупок."""
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = ShoppingBasketsSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.add_object(ShoppingBasket, request.user, pk)

    @shopping_cart.mapping.delete
    def del_shopping_cart(self, request, pk=None):
        """Убрать из листа покупок."""
        shopping_cart_item = ShoppingBasket.objects.filter(
            user=request.user, recipe=pk)
        if shopping_cart_item.exists():
            shopping_cart_item.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        else:
            return Response({'detail': 'Элемент листа покупок не найден.'},
                            status=HTTPStatus.NOT_FOUND)

    @transaction.atomic()
    def add_object(self, model, user, pk):
        """Добавление объектов для избранного/спсика покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = AddingRecipesSerializer(recipe)
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @transaction.atomic()
    def delete_object(self, model, user, pk):
        """Удаление объектов для избранного/спсика покупок."""
        model.objects.filter(user=user, recipe__id=pk).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        methods=["GET"], detail=False, permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Скачать файл листа покупок."""
        ingredients = (
            IngredientInRecipe.objects.filter(recipe__list__user=request.user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .order_by("ingredient__name")
            .annotate(total=Sum("amount"))
        )

        content = self.generate_shopping_cart_content(ingredients)

        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = f"attachment; filename={FILE_NAME}"
        return response


class FollowViewSet(UserViewSet):
    """Класс взаимодействия с моделью Follow. Вьюсет подписок."""

    @action(methods=['POST'], detail=True,
            permission_classes=(IsAuthenticated,))
    @transaction.atomic()
    def subscribe(self, request, id=None):
        """Подписка на автора."""
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {
            'user': user.id,
            'author': author.id,
        }
        serializer = CheckFollowSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        result = Follow.objects.create(user=user, author=author)
        serializer = FollowSerializer(result, context={'request': request})
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @subscribe.mapping.delete
    @transaction.atomic()
    def del_subscribe(self, request, id=None):
        """Отписка от автора."""
        user = request.user
        author = get_object_or_404(User, pk=id)

        subscription = user.follower.filter(author=author)

        if subscription.exists():
            subscription.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        else:
            return Response({'detail': 'Подписка не найдена.'},
                            status=HTTPStatus.NOT_FOUND)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Подписки."""
        user = request.user
        queryset = user.follower.annotate(
            recipes_count=Count('author__recipes'))
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
