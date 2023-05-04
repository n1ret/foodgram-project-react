from rest_framework import serializers
from .models import Ingredient, Tag, Recipe, UsableIngredient
from users.serializer import UserSerializer
from django.conf import settings
from drf_base64.fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
    
    def __str__(self) -> str:
        return self.name


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class UsableIngredientSeializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient_id')

    class Meta:
        model = UsableIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CustomBase64ImageField(Base64ImageField):
    def to_representation(self, value):
        if not value:
            return None

        try:
            url = value.url
        except AttributeError:
            return None
        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url).replace(
                'backend:8000', settings.IP_ADDR)
        return url


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = UsableIngredientSeializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField('is_favorite')
    is_in_shopping_cart = serializers.SerializerMethodField(
        'recipe_is_in_shopping_cart'
    )
    image = CustomBase64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'ingredients', 'tags', 'cooking_time', 'is_favorited',
            'is_in_shopping_cart'
        )
    
    def validate(self, attrs):
        for i in self.initial_data.get('ingredients'):
            if (
                type(i) != dict or 'id' not in i or 'amount' not in i or
                not Ingredient.objects.filter(id=i.get('id')).exists()
            ):
                raise serializers.ValidationError('Ingredients invalid')
        for i in self.initial_data.get('tags'):
            if not Tag.objects.filter(id=i).exists():
                raise serializers.ValidationError('Tag invalid')
        return attrs
    
    def create(self, validated_data):
        user = self.context.get("request").user
        ingredients = []
        if 'ingredients' in self.initial_data:
            ingredients = self.initial_data.pop('ingredients')
        tags = []
        if 'tags' in self.initial_data:
            tags = self.initial_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data, author=user)

        for tag in tags:
            recipe.tags.add(tag)
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient = IngredientSerializer(
                Ingredient.objects.get(id=ingredient.get('id'))
            )
            data = ingredient.data
            UsableIngredient.objects.create(
                ingredient_id=data.pop('id'), **data, amount=amount,
                recipe=recipe
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients = []
        if 'ingredients' in self.initial_data:
            instance.ingredients.all().delete()
            ingredients = self.initial_data.pop('ingredients')
        tags = []
        if 'tags' in self.initial_data:
            instance.tags.clear()
            tags = self.initial_data.pop('tags')

        for tag in tags:
            instance.tags.add(tag)
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient = IngredientSerializer(
                Ingredient.objects.get(id=ingredient.get('id'))
            )
            data = ingredient.data
            UsableIngredient.objects.create(
                ingredient_id=data.pop('id'), **data, amount=amount,
                recipe=instance
            )

        return super().update(instance, validated_data)
    
    def is_favorite(self, instance):
        return (
            self.context.get('request').user in
            instance.favorite.all()
        )
    
    def recipe_is_in_shopping_cart(self, instance):
        return (
            self.context.get('request').user in
            instance.shopping_cart.all()
        )


class RecipeDeserializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
