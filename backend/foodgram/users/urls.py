from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyView, UserViewSet, PasswordView

router = DefaultRouter()
router.register('', UserViewSet)
router.register('set_password', PasswordView, basename='change-password')

urlpatterns = [
    path('me/', MyView.as_view()),
    path('', include(router.urls))
]
