from django.contrib import admin
from django.urls import path, include

from .views import DeauthView, CustomObtainAuthToken, import_ingredients

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/login/', CustomObtainAuthToken.as_view()),
    path('api/auth/token/logout/', DeauthView.as_view()),
    path('api/', include('api.urls')),
    path('api/users/', include('users.urls')),
]

import_ingredients()
