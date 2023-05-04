from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IngredientsViewSet, RecipeViewSet, ShoppingCartGet, TagViewSet,
    ShoppingCartView, FavoriteView, SubscribeView, SubscriptionsGetView
)

router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('ingredients', IngredientsViewSet, 'ingredients')

urlpatterns = [
    path('recipes/download_shopping_cart/', ShoppingCartGet.as_view()),
    path('recipes/<int:recipe_id>/shopping_cart/', ShoppingCartView.as_view()),
    path('recipes/<int:recipe_id>/favorite/', FavoriteView.as_view()),
    path('users/subscriptions/', SubscriptionsGetView.as_view()),
    path('users/<int:user_id>/subscribe/', SubscribeView.as_view()),
    path('', include(router.urls)),
]
