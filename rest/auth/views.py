from django.contrib.auth import authenticate, login, logout
from rest_framework import response, status
from wq.db.rest import util, views, renderers, app

class LoginView(views.View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            user_dict = util.user_dict(request.user)
            user_dict['id'] = request.user.pk
            return {
                'user': user_dict,
                'config': util.get_config(request.user)
            }
        else:
            return {}

    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            user_dict = util.user_dict(user)
            user_dict['id'] = user.pk
            return {
                'user':   user_dict,
                'config': util.get_config(user)
            }
        else:
            raise response.ErrorResponse(status.HTTP_401_UNAUTHORIZED, {
                'errors': ["Invalid username or password"]
            })

class LogoutView(views.View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            logout(request)
            return True
        else:
            return {}

def get_user(renderer, obj):
    user = renderer.view.request.user
    if user.is_authenticated():
        return util.user_dict(user)
    return None

app.router.add_page_config('login',  {'name': 'Log in',  'url': 'login'})
app.router.add_page_config('logout', {'name': 'Log out', 'url': 'logout'})

renderers.HTMLRenderer.register_context_default('user', get_user)
