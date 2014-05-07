from wq.db.rest import app
from .views import LoginView, LogoutView, UserViewSet
from django.contrib.auth.models import User

app.router.add_page('login', {'url': 'login'}, LoginView)
app.router.add_page('logout', {'url': 'logout'}, LogoutView)

app.router.register_viewset(User, UserViewSet)
