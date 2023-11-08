from http import HTTPStatus
from io import BytesIO

# from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Sum
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingBasket, Tag)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly, IsAdminOrReadOnly
from .serializers import (AddFavoritesSerializer, CreateRecipeSerializer,
                          FollowSerializer, IngredientsSerializer,
                          ReadRecipesSerializer, ShoppingBasketsSerializer,
                          TagsSerializer)


class ListRetrieveViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    permission_classes = (IsAdminOrReadOnly,)


class TagsViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class IngredientsViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_class = IngredientFilter


class RecipesViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadRecipesSerializer
        return CreateRecipeSerializer

    def get_queryset(self):
        base_queryset = (
            Recipe.objects.select_related("author")
            .prefetch_related("tags", "ingredients")
            .annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=OuterRef("author_id"),
                        recipe__pk=OuterRef("pk")
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingBasket.objects.filter(
                        user=OuterRef("author_id"),
                        recipe__pk=OuterRef("pk")
                    )
                ),
            )
        )
        if self.request.user.is_authenticated:
            return base_queryset.filter(author=self.request.user)
        return base_queryset

    def favorite(self, request, pk):
        """Метод для управления избранными подписками """

        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': f'Повторно - \"{recipe.name}\" добавить нельзя,'
                               f'он уже есть в избранном у пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = AddFavoritesSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            obj = Favorite.objects.filter(user=user, recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': f'В избранном нет рецепта \"{recipe.name}\"'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["POST"],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = ShoppingBasketsSerializer(
            data={"user": user.id, "recipe": recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=HTTPStatus.CREATED)

    @shopping_cart.mapping.delete
    def del_shopping_cart(self, request, pk=None):
        user = request.user
        deleted_count = ShoppingBasket.objects.filter(
            user=user, recipe__pk=pk).delete()
        if deleted_count[0] == 0:
            return Response({"error": "Не существует"},
                            status=HTTPStatus.BAD_REQUEST)
        return Response(status=HTTPStatus.NO_CONTENT)

    def generate_shopping_list(self, user):
        ingredients = (
            IngredientInRecipe.objects.filter(recipe__list__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .order_by("ingredient__name")
            .annotate(total=Sum("amount"))
        )

        buffer = BytesIO()
        with buffer:
            buffer.write("Список покупок:\n\n".encode("utf-8"))
            for ingredient in ingredients:
                line = (
                    f"{ingredient['ingredient__name']} - "
                    f"{ingredient['total']}/"
                    f"{ingredient['ingredient__measurement_unit']}\n"
                )
                buffer.write(line.encode("utf-8"))

        return buffer

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user
        buffer = self.generate_shopping_list(user)

        response = Response(content_type="text/plain")
        response["Content-Disposition"] = (
            "attachment; filename=shopping-list.txt")
        response.write(buffer.getvalue())
        return response


class FollowViewSet(UserViewSet):
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        serializer = FollowSerializer(
            data={"user": user.id, "author": author.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=HTTPStatus.CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        user = request.user
        deleted_count = Follow.objects.filter(
            user=user, author__pk=id).delete()
        if deleted_count[0] == 0:
            return Response({"error": "Не существует"},
                            status=HTTPStatus.BAD_REQUEST)
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user).annotate(
            recipes_count=Count("author__recipes")
        )
        serializer = FollowSerializer(queryset, many=True)
        return Response(serializer.data)
