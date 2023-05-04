from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.status import HTTP_204_NO_CONTENT
from json import load
from sys import argv

from api.models import Ingredient


class DeauthView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"success": ("Successfully logged out")}, status=HTTP_204_NO_CONTENT)


class CustomAuthTokenSerializer(AuthTokenSerializer):
    username = serializers.CharField(
        label="Username",
        write_only=True,
        required=False
    )
    email = serializers.CharField(
        label='Email',
        write_only=True,
        required=False
    )

    def validate(self, attrs):
        email = attrs.get('email', None)
        username = attrs.get('username', None)
        password = attrs.get('password')

        if password:
            if email:
                user = authenticate(request=self.context.get('request'),
                                    email=email, password=password)
            elif username:
                user = authenticate(request=self.context.get('request'),
                                    username=username, password=password)
            else:
                msg = 'Must include "username" or "email"'
                raise serializers.ValidationError(msg, code='authorization')
            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "username" and "password"'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class CustomObtainAuthToken(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


def import_ingredients():
    if 'createsuperuser' in argv and not Ingredient.objects.all().exists():
        with open('foodgram/ingredients.json', 'r') as file:
            data = load(file)
        for ingredient in data:
            Ingredient.objects.create(**ingredient)
