from django.contrib import admin
from django.db.models import Count

from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingBasket, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "measurement_unit")
    list_filter = ("name",)
    list_editable = ("recipe", "ingredient", "amount")
    search_fields = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "author", "number_of_favorites", "created")
    list_editable = ("name",)
    list_filter = ("author", "name", "tags")
    search_fields = ("name",)

    def number_of_favorites(self, obj):
        return obj.favorites.count()

    def get_queryset(self, request):
        return (
            super().get_queryset(request).annotate(
                favorites_count=Count("favorites"))
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "slug", "color")
    list_editable = ("name", "slug", "color")


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "recipe", "ingredient", "amount")
    list_editable = ("recipe", "ingredient", "amount")


@admin.register(ShoppingBasket)
class ShoppingBasketAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    list_editable = ("user", "recipe")
    search_fields = ("user", "recipe")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    list_editable = ("user", "recipe")
    search_fields = ("name", "recipe")
