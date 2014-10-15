from wq.db.rest import app
from .views import LoginView, LogoutView, UserViewSet
from .serializers import UserSerializer, SocialAuthSerializer, HAS_SOCIAL_AUTH
from django.contrib.auth.models import User

app.router.add_page('login', {'url': 'login'}, LoginView)
app.router.add_page('logout', {'url': 'logout'}, LogoutView)

app.router.register_viewset(User, UserViewSet)
app.router.register_serializer(User, UserSerializer)

if HAS_SOCIAL_AUTH:
    # Configure UserSocialAuth as nested serializer for User
    # (without actually registering it)
    from social.apps.django_app.default.models import UserSocialAuth
    app.router.register_serializer(UserSocialAuth, SocialAuthSerializer)
    app.router.register_config(UserSocialAuth, {'url': 'social_auth'})
