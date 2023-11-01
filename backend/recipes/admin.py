from django.contrib import admin
from django.db.models import Count, Prefetch

from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingBasket, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "measurement_unit")
    list_filter = ("name",)
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipe')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "author", "number_of_favorites", "created")
    list_editable = ("name",)
    list_filter = ("author", "name", "tags")
    search_fields = ("name",)

    def number_of_favorites(self, obj):
        return obj.favorites_count

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('author')
            .prefetch_related(Prefetch('tags'), Prefetch('ingredients'))
            .annotate(favorites_count=Count('favorites'))
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "slug", "color")
    list_editable = ("name", "slug", "color")


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")


@admin.register(ShoppingBasket)
class ShoppingBasketAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    search_fields = ("user__username", "recipe__name")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
