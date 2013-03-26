from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from wq.db.rest import app
from wq.db.rest.views import View

class LoginView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            user_dict = app.router.serialize(request.user)
            user_dict['id'] = request.user.pk
            return Response({
                'user': user_dict,
                'config': app.router.get_config(request.user)
            })
        else:
            return Response({})

    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            user_dict = app.router.serialize(user)
            user_dict['id'] = user.pk
            return Response({
                'user':   user_dict,
                'config': app.router.get_config(user)
            })
        else:
            raise AuthenticationFailed(detail="Invalid username or password")

class LogoutView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            logout(request)
        return Response({})

app.router.add_page('login',  {'name': 'Log in',  'url': 'login'}, LoginView)
app.router.add_page('logout', {'name': 'Log out', 'url': 'logout'}, LogoutView)
