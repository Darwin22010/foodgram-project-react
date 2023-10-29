from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = get_user_model()


class Ingredients(models.Model):
    name = models.CharField(
        verbose_name="Название ингредиента", max_length=300
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения", max_length=150
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}."

class Tags(models.Model):
    name = models.CharField(
        verbose_name='Название тэга',
        max_length=100,
        unique=True
    )
    color = models.CharField(
        verbose_name="Цвет HEX",
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Несоответсвует формату HEX'
            )
        ],
    )
    slug = models.SlugField(
        verbose_name='Уникальный слаг',
        max_length=100,
        unique=True,
    )

    class Meta:

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'color', 'slug'),
                name='unique_tags',
            ),
        )

    def __str__(self):

        return self.name
class Recipes(models.Model):

    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes',
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=300,
    )
    image = models.ImageField(
        verbose_name='Фотография',
        upload_to='recipes/',
        blank=True
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        verbose_name='Ингредиенты',
        related_name='recipes',
        through='IngredientsInRecipes',
    )
    tags = models.ManyToManyField(
        Tags,
        verbose_name='Теги',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(1, message='Не меньше 1'),
        ],
        help_text='Время в минутах'
    )
    created = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:

        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created',)

    def __str__(self):

        return self.name

class ShoppingBaskets(models.Model):

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="list",
    )
    recipe = models.ForeignKey(
        Recipes, on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="list",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        ordering = ("-id",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_list_user"
            )
        ]

    def __str__(self):

        return f'{self.user} {self.recipe}'

class Favorites(models.Model):

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipes, on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )

    class Meta:

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]

    def __str__(self):

        return f'{self.user} {self.recipe}'

class IngredientsInRecipes(models.Model):

    recipe = models.ForeignKey(
        Recipes, on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredient_list',
    )
    ingredient = models.ForeignKey(
        Ingredients, on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='in_recipe'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(1, message='Не меньше 1'),
        ]
    )

    class Meta:

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredients_in_the_recipe'
            )
        ]

    def __str__(self):

        return f'{self.ingredient} {self.recipe}' 