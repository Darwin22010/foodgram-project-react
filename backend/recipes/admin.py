from django.contrib import admin

from .models import (Favorites, Ingredients, IngredientsInRecipes, Recipes,
                     ShoppingBaskets, Tags)


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "measurement_unit")
    search_fields = ("name",)


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "author", "number_of_favorites", "created")
    list_filter = ("author", "name", "tags")
    search_fields = ("name",)

    def number_of_favorites(self, obj):
        return obj.favorites.count()


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "color", "slug")


@admin.register(IngredientsInRecipes)
class IngredientsInRecipes(admin.ModelAdmin):
    list_display = ("pk", "recipe", "ingredient", "amount")


@admin.register(ShoppingBaskets)
class ShoppingBasketsAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
