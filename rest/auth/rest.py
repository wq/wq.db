from wq.db import rest
from .views import LoginView, LogoutView
from .serializers import UserSerializer
from django.contrib.auth.models import User

rest.router.add_page('login', {'url': 'login'}, LoginView)
rest.router.add_page('logout', {'url': 'logout'}, LogoutView)

# Configure UserSerializer (without actually registering User model)
rest.router.register_serializer(User, UserSerializer)
