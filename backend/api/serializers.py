from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingBasket, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import Follow, User


class CustomUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    class Meta:
        model = User
        fields = ("id", "email", "username",
                  "first_name", "last_name", "password")


class CustomUserListSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", "is_subscribed")
        read_only_fields = ("is_subscribed",)

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        return not user.is_anonymous and user.follower.filter(
            author=obj.id).exists()


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class ReadRecipesSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True)
    author = CustomUserListSerializer()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            "id",
            "name",
            "measurement_unit",
            amount=serializers.F("ingredients_amount__amount"),
        )


class WriteRecipeseSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    ingredients = serializers.ListSerializer(child=serializers.DictField())
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("ingredients", "tags", "name",
                  "image", "text", "cooking_time")
        read_only_fields = ("author",)

    def validate(self, data):
        ingredients = data["ingredients"]
        ingredient_ids = [item["id"] for item in ingredients]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться.")
        for item in ingredients:
            if item["amount"] < 1:
                raise serializers.ValidationError("Не меньше 1")
        return data

    def validate_cooking_time(self, time):
        if int(time) < 1:
            raise serializers.ValidationError("Не меньше 1")
        return time

    def add_ingredients_and_tags(self, instance, **validate_data):
        ingredients = validate_data["ingredients"]
        tags = validate_data["tags"]
        instance.ingredients.set(ingredients)
        instance.tags.set(*tags)

        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    recipe=instance,
                    ingredient_id=ingredient.get("id"),
                    amount=ingredient.get("amount"),
                )
                for ingredient in ingredients
            ]
        )
        return instance

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        for item in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=recipe, ingredient_id=item["id"], amount=item["amount"]
            )
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        ingredients_data = validated_data.pop("ingredients")
        for item in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=instance, ingredient_id=item["id"],
                amount=item["amount"]
            )
        return super().update(instance, validated_data)


class AddingRecipesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField()

    class Meta:
        model = Follow
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        queryset = obj.author.recipes.all()
        if limit:
            queryset = queryset[: int(limit)]
        return AddingRecipesSerializer(queryset, many=True).data


class CheckFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("user", "author")

    def validate(self, obj):
        user = obj["user"]
        author = obj["author"]
        subscribed = user.follower.filter(author=author).exists()

        if self.context.get("request").method == "POST":
            if user == author:
                raise serializers.ValidationError(
                    "Ошибка, на себя подписка не разрешена"
                )
            if subscribed:
                raise serializers.ValidationError("Ошибка, вы уже подписались")
        if self.context.get("request").method == "DELETE":
            if user == author:
                raise serializers.ValidationError(
                    "Ошибка, отписка от самого себя не разрешена"
                )
            if not subscribed:
                raise serializers.ValidationError(
                    {"errors": "Ошибка, вы уже отписались"}
                )
        return obj


class FavoritesSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ("user", "recipe")

    def validate(self, obj):
        user = self.context["request"].user
        recipe = obj["recipe"]
        favorite = user.favourites.filter(recipe=recipe).exists()

        if self.context.get("request").method == "POST" and favorite:
            raise serializers.ValidationError(
                "Этот рецепт уже добавлен в избранном")
        if self.context.get("request").method == "DELETE" and not favorite:
            raise serializers.ValidationError(
                "Этот рецепт отсутствует в избранном")
        return obj


class ShoppingBasketsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingBasket
        fields = ("user", "recipe")

    def validate(self, obj):
        user = self.context["request"].user
        recipe = obj["recipe"]
        shop_list = user.list.filter(recipe=recipe).exists()

        if self.context.get("request").method == "POST" and shop_list:
            raise serializers.ValidationError(
                "Этот рецепт уже в списке покупок.")
        if self.context.get("request").method == "DELETE" and not shop_list:
            raise serializers.ValidationError("Рецепт не в списке покупок.")
        return obj
