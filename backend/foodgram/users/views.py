from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from .serializer import UserSerializer
from .models import User


class PageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'


class MyView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(
            request.user, context={'request': request}).data
        )


class PasswordView(GenericViewSet, mixins.CreateModelMixin):
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        self.object = self.request.user
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if self.object.check_password(serializer.data.current_password):
                return Response({"current_password": ["Current password not equal new password."]}, status=status.HTTP_400_BAD_REQUEST)
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_204_NO_CONTENT,
                'message': 'Пароль изменён',
                'data': []
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(GenericViewSet, mixins.ListModelMixin, PageNumberPagination,
                  mixins.CreateModelMixin, mixins.RetrieveModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination

    def retrieve(self, request, *args, **kwargs):
        if not request.user:
            return PermissionDenied('Вы не зарегестрированы')
        return super().retrieve(request, *args, **kwargs)
