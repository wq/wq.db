from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.middleware import csrf
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from wq.db.rest import app
from wq.db.rest.views import View, InstanceModelView


class AuthView(View):
    def user_info(self, request):
        user_dict = app.router.serialize(request.user)
        user_dict['id'] = request.user.pk
        return Response({
            'user': user_dict,
            'config': app.router.get_config(request.user),
            'csrftoken': csrf.get_token(request),
        })

    def csrf_info(self, request):
        response = {}
        token = csrf.get_token(request)
        if token:
            response['csrftoken'] = token
        return Response(response)


class LoginView(AuthView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return self.user_info(request)
        else:
            return self.csrf_info(request)

    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return self.user_info(request)
        else:
            raise AuthenticationFailed(detail="Invalid username or password")


class LogoutView(AuthView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            logout(request)
        return self.csrf_info(request)


class UserDetailView(InstanceModelView):
    def get_slug_field(self):
        return 'username'

app.router.add_page('login', {'name': 'Log in', 'url': 'login'}, LoginView)
app.router.add_page('logout', {'name': 'Log out', 'url': 'logout'}, LogoutView)

app.router.register_views(User, listview=None, instanceview=UserDetailView)
