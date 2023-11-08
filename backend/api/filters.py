from django.core.exceptions import ValidationError
from django_filters import (FilterSet, ModelMultipleChoiceFilter, filters,
                            rest_framework)
from recipes.models import Ingredient, Recipe, Tag


class TagsMultipleChoiceField(filters.AllValuesMultipleFilter):
    """Класс для фильтрации обьектов Tags."""

    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages["required"], code="required"
            )
        for val in value:
            if val in self.choices and not self.valid_value(val):
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": val},
                )


class TagsFilter(filters.AllValuesMultipleFilter):
    """Класс для фильтрации обьектов Tags."""

    field_class = TagsMultipleChoiceField


class IngredientFilter(FilterSet):
    name = rest_framework.CharFilter(lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(FilterSet):
    is_favorite = filters.BooleanFilter(method="filter_favorites")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_shopping_cart")
    author = filters.AllValuesMultipleFilter(
        field_name="author__id", label="Автор")
    tags = ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )

    def filter_favorites(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user_id=self.request.user.id)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(
                shopping_recipe__user_id=self.request.user.id)
        return queryset

    class Meta:
        model = Recipe
        fields = ("author", "tags", "is_in_shopping_cart", "is_favorite")
