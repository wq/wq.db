from wq.db import rest
from .views import LoginView, LogoutView, UserViewSet
from .serializers import UserSerializer, HAS_SOCIAL_AUTH
from django.contrib.auth.models import User

rest.router.add_page('login', {'url': 'login'}, LoginView)
rest.router.add_page('logout', {'url': 'logout'}, LogoutView)

rest.router.register_viewset(User, UserViewSet)
rest.router.register_serializer(User, UserSerializer)

if HAS_SOCIAL_AUTH:
    # Configure UserSocialAuth as nested serializer for User
    # (without actually registering it)
    from social.apps.django_app.default.models import UserSocialAuth
    from .serializers import SocialAuthSerializer
    rest.router.register_serializer(UserSocialAuth, SocialAuthSerializer)
    rest.router.register_config(UserSocialAuth, {'url': 'social_auth'})
