from django.contrib import admin
from django.db.models import Count

from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingBasket, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'pk', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'pk', 'author', 'number_of_favorites', 'created')
    list_filter = ('author', 'tags')
    search_fields = ('author', 'name', 'tags')

    def number_of_favorites(self, obj):
        return obj.favorites_count

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('author')
            .prefetch_related('tags', 'ingredients')
            .annotate(favorites_count=Count('favorites'))
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'pk', 'slug', 'color')
    search_fields = ('name',)


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'pk', 'ingredient', 'amount')
    list_display_links = ['recipe', 'ingredient']
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(ShoppingBasket)
class ShoppingBasketAdmin(admin.ModelAdmin):
    list_display = ('user', 'pk', 'recipe')
    list_display_links = ['user', 'recipe']
    search_fields = ('user__username', 'recipe__name')

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('user', 'recipe')
        )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'pk', 'recipe')
    list_display_links = ['user', 'recipe']
    search_fields = ('user__username', 'recipe__name')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'recipe')
        return queryset
