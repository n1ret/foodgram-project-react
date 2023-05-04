from django.db import models
from users.models import User


class Ingredient(models.Model):
    name = models.TextField()
    measurement_unit = models.TextField()

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.TextField()
    collor = models.TextField()
    slug = models.SlugField()

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes'
    )
    name = models.TextField()
    image = models.ImageField(upload_to='recipes/images/')
    text = models.TextField()
    tags = models.ManyToManyField(Tag)
    cooking_time = models.IntegerField()
    favorite = models.ManyToManyField(User, related_name='favorites')
    shopping_cart = models.ManyToManyField(User, related_name='shopping_cart')

    class Meta:
        ordering = ['-id']
    
    def __str__(self) -> str:
        return f'{self.name} {self.id}'


class UsableIngredient(models.Model):
    ingredient_id = models.IntegerField()
    name = models.TextField()
    measurement_unit = models.TextField()
    amount = models.FloatField()
    recipe = models.ForeignKey(
        Recipe, related_name='ingredients', on_delete=models.CASCADE
    )
