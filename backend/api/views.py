from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorites, Ingredients, IngredientsInRecipes,
                            Recipes, ShoppingBaskets, Tags)
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly, IsAdminOrReadOnly
from .serializers import (FollowSerializer, IngredientsSerializer,
                          ReadRecipesSerializer, TagsSerializer,
                          WriteRecipeseSerializer)

User = get_user_model()


class ListRetrieveViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    permission_classes = (IsAdminOrReadOnly,)


class TagsViewSet(ListRetrieveViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class IngredientsViewSet(ListRetrieveViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_class = IngredientFilter


class RecipesViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadRecipesSerializer
        return WriteRecipeseSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Recipes.objects.annotate(
                is_favorited=Exists(
                    Favorites.objects.filter(
                        user=self.request.user, recipe__pk=OuterRef("pk")
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingBaskets.objects.filter(
                        user=self.request.user, recipe__pk=OuterRef("pk")
                    )
                ),
            )
        else:
            return Recipes.objects.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField()),
            )

    @transaction.atomic()
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["POST"],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipes, pk=pk)
        if Favorites.objects.filter(user=user, recipe=recipe).exists():
            return Response(status=HTTPStatus.OK)
        Favorites.objects.create(user=user, recipe=recipe)
        return Response(status=HTTPStatus.CREATED)

    @favorite.mapping.delete
    def del_favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipes, pk=pk)
        Favorites.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=True, methods=["POST"],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipes, pk=pk)
        if ShoppingBaskets.objects.filter(user=user, recipe=recipe).exists():
            return Response(status=HTTPStatus.OK)
        ShoppingBaskets.objects.create(user=user, recipe=recipe)
        return Response(status=HTTPStatus.CREATED)

    @shopping_cart.mapping.delete
    def del_shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipes, pk=pk)
        ShoppingBaskets.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            IngredientsInRecipes.objects.filter(recipe__list__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .order_by("ingredient__name")
            .annotate(total=Sum("amount"))
        )
        result = "Список покупок:\n\n"
        result += "\n".join(
            (
                f'{ingredient["ingredient__name"]} - {ingredient["total"]}/'
                f'{ingredient["ingredient__measurement_unit"]}'
                for ingredient in ingredients
            )
        )
        response = Response(result, content_type="text/plain")
        response[
            "Content-Disposition"
        ] = "attachment; filename=shopping-list.txt"
        return response


class FollowViewSet(UserViewSet):
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if Follow.objects.filter(user=user, author=author).exists():
            return Response(status=HTTPStatus.OK)
        Follow.objects.create(user=user, author=author)
        return Response(status=HTTPStatus.CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        Follow.objects.filter(user=user, author=author).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        serializer = FollowSerializer(queryset, many=True)
        return Response(serializer.data)
