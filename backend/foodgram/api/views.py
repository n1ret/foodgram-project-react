from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

from api.models import Tag, Recipe, Ingredient
from .serializers import (
    RecipeSerializer, TagSerializer, IngredientSerializer, RecipeDeserializer
)
from users.models import User
from users.serializer import UserSerializer


class PageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'


class IsAuthenticatedForCurMethod(BasePermission):
    def has_permission(self, request, _):
        if (request.method in ('POST', 'PATCH', 'DEL') and
            not request.user.is_authenticated):
            return False
        return True


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        if 'name' in self.request.query_params:
            queryset = queryset.filter(
                name__startswith=self.request.query_params.get('name'))
        return queryset


class RecipeViewSet(ModelViewSet, PageNumberPagination):
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedForCurMethod,)
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = Recipe.objects.all()
        if int(self.request.query_params.get('is_favorited', 0)):
            queryset &= self.request.user.favorites.all()
        if int(self.request.query_params.get('is_in_shopping_cart', 0)):
            queryset &= self.request.user.shopping_cart.all()
        if 'tags' in self.request.query_params:
            new_queryset = queryset.none()
            for i in self.request.query_params.getlist('tags'):
                new_queryset = new_queryset.union(
                    queryset.filter(tags__slug=i))
            queryset = new_queryset
        return queryset

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied('Изменение чужого рецепта запрещено!')
        return super().perform_update(serializer)
    
    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied('Удаление чужого рецепта запрещено!')
        return super().perform_destroy(instance)


class ShoppingCartView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return Recipe.objects.get(id=pk)

    def post(self, request, recipe_id):
        recipe = self.get_object(recipe_id)
        if recipe.shopping_cart.filter(id=request.user.id).exists():
            raise ParseError('This recipe alredy in your shopping cart.')
        recipe.shopping_cart.add(request.user)
        serializer = RecipeSerializer(recipe, context={'request': request})
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )
    
    def delete(self, request, recipe_id):
        recipe = self.get_object(recipe_id)
        if not recipe.shopping_cart.filter(id=request.user.id).exists():
            raise ParseError('This recipe is not in your shopping cart.')
        recipe.shopping_cart.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartGet(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = request.user.shopping_cart.all()
        ingredients = {}
        for recipe in queryset:
            cur_ingredients = RecipeSerializer(
                recipe, context={'request': request}).data.get('ingredients')
            for ingredient in cur_ingredients:
                if ingredient.get('name') not in ingredients:
                    ingredients[ingredient.get('name')] = {
                        'amount': ingredient.get('amount'),
                        'measurement_unit': ingredient.get('measurement_unit')
                    }
                else:
                    ingredients[
                        ingredient.get('name')
                    ]['amount'] += ingredient.get('amount')
        txt = ''
        for name, value in ingredients.items():
            txt += f"{name} ({value['measurement_unit']}) - {value['amount']}"
            txt += '\n'

        response = HttpResponse(txt, content_type='text/plain; charset=utf8')
        response[
            'Content-Disposition'] = 'attachment; filename=shopping_cart.txt'
        return response


class FavoriteView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return Recipe.objects.get(id=pk)

    def post(self, request, recipe_id):
        recipe = self.get_object(recipe_id)
        if recipe.favorite.filter(id=request.user.id).exists():
            raise ParseError('This recipe alredy in favorite.')
        recipe.favorite.add(request.user)
        serializer = RecipeSerializer(recipe, context={'request': request})
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )
    
    def delete(self, request, recipe_id):
        recipe = self.get_object(recipe_id)
        if not recipe.favorite.filter(id=request.user.id).exists():
            raise ParseError('This recipe is not in your favorite.')
        recipe.favorite.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return User.objects.get(id=pk)

    def post(self, request, user_id):
        user = self.get_object(user_id)
        if (user.subscribers.filter(id=request.user.id).exists() or
            user == request.user):
            raise ParseError('Unable to follow this user.')
        user.subscribers.add(request.user)
        user_data = UserSerializer(user, context={'request': request}).data
        recipes = RecipeDeserializer(user.recipes.all(), many=True).data
        user_data['recipes'] = recipes
        user_data['recipes_count'] = user.recipes.count()
        return Response(
            user_data, status=status.HTTP_201_CREATED
        )
    
    def delete(self, request, user_id):
        user = self.get_object(user_id)
        if (not user.subscribers.filter(id=request.user.id).exists()):
            raise ParseError('This user is not in your subscriptions.')
        user.subscribers.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsGetView(APIView, PageNumberPagination):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        subscriptions = request.user.subscriptions.all()

        if 'recipes_limit' in request.query_params:
            recipes_limit = int(request.query_params.get('recipes_limit'))
            for user in subscriptions:
                if user.recipes.count() > recipes_limit:
                    subscriptions = subscriptions.exclude(id=user.id)

        results = self.paginate_queryset(subscriptions, request, view=self)
        serializer = UserSerializer(
            results, many=True, context={'request': request})
        subscriptions_list = list(subscriptions)
        for i in range(len(serializer.data)):
            serializer.data[i]['recipes'] = RecipeDeserializer(
                subscriptions_list[i].recipes.all(), many=True,
            ).data
            serializer.data[i]['recipes_count'] = subscriptions_list[
                i].recipes.count()
        return self.get_paginated_response(serializer.data)
