from django.contrib.auth import authenticate, login, logout
from django.middleware import csrf
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from wq.db import rest
from wq.db.rest.models import get_object_id
from wq.db.rest.views import SimpleViewSet


class AuthView(SimpleViewSet):
    def user_info(self, request):
        user_dict = rest.router.serialize(request.user)
        user_dict['id'] = get_object_id(request.user)
        return Response({
            'user': user_dict,
            'config': rest.router.get_config(request.user),
            'csrftoken': csrf.get_token(request),
        })

    def csrf_info(self, request):
        response = {}
        token = csrf.get_token(request)
        if token:
            response['csrftoken'] = token
        return Response(response)


class LoginView(AuthView):
    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return self.user_info(request)
        else:
            return self.csrf_info(request)

    def create(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return self.user_info(request)
        else:
            raise AuthenticationFailed(detail="Invalid username or password")


class LogoutView(AuthView):
    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return self.csrf_info(request)
