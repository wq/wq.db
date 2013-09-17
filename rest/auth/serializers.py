from wq.db.rest import app
from wq.db.rest.serializers import ModelSerializer
from django.contrib.auth.models import User
from django.conf import settings


class UserSerializer(ModelSerializer):
    def to_native(self, instance):
        result = super(UserSerializer, self).to_native(instance)
        if ('social_auth' in settings.INSTALLED_APPS
                and 'social_auth' in result):
            if len(result['social_auth']) > 0:
                result['social_auth'] = {'accounts': result['social_auth']}
            else:
                result['social_auth'] = None
        return result

    class Meta:
        exclude = ('id', 'password')


class SocialAuthSerializer(ModelSerializer):
    def to_native(self, instance):
        return {
            'provider_id': unicode(instance.provider),
            'provider_label': instance.provider.title(),
            'id': instance.pk,
            'label': instance.uid,
            'can_disconnect': type(instance).allowed_to_disconnect(
                user=instance.user,
                backend_name=instance.provider,
                association_id=instance.pk
            )
        }

app.router.register_serializer(User, UserSerializer)
if 'social_auth' in settings.INSTALLED_APPS:
    from social_auth.models import UserSocialAuth
    app.router.register_serializer(UserSocialAuth, SocialAuthSerializer)
