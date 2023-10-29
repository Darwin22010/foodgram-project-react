from django_filters import (FilterSet, ModelMultipleChoiceFilter, filters,
                            rest_framework)
from recipes.models import Ingredients, Recipes, Tags


class IngredientFilter(FilterSet):
    name = rest_framework.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredients
        fields = ('name', )

class RecipeFilter(FilterSet):
    is_favorite = filters.BooleanFilter(method="filter_favorites")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_shopping_cart")
    author = filters.AllValuesMultipleFilter(field_name="author__id", label="Автор")
    tags = ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tags.objects.all(),
    )

    def filter_favorites(self, queryset, name, value):
        if value:
            user = self.request.user
            return queryset.filter(favorites__user_id=user.id)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        if value:
            user = self.request.user
            return queryset.filter(shopping_recipe__user_id=user.id)
        return queryset

    class Meta:
        model = Recipes
        fields = ("author", "tags", "is_in_shopping_cart", "is_favorite")
