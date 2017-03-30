from wq.db.rest.serializers import ModelSerializer
from django.conf import settings


HAS_SOCIAL_AUTH = ('social.apps.django_app.default' in settings.INSTALLED_APPS)
if HAS_SOCIAL_AUTH:
    from social.apps.django_app.default.models import UserSocialAuth

    class SocialAuthSerializer(ModelSerializer):
        def to_representation(self, instance):
            return {
                'provider_id': str(instance.provider),
                'provider_label': instance.provider.title(),
                'id': instance.pk,
                'label': instance.uid,
                'can_disconnect': type(instance).allowed_to_disconnect(
                    user=instance.user,
                    backend_name=instance.provider,
                    association_id=instance.pk
                )
            }

        class Meta:
            model = UserSocialAuth


class UserSerializer(ModelSerializer):
    if HAS_SOCIAL_AUTH:
        social_auth = SocialAuthSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        result = super(UserSerializer, self).to_representation(instance)
        if (HAS_SOCIAL_AUTH and 'social_auth' in result):
            if len(result['social_auth']) > 0:
                result['social_auth'] = {'accounts': result['social_auth']}
            else:
                result['social_auth'] = None
        return result

    class Meta:
        exclude = ('id', 'password', 'user_permissions', 'groups',)
        read_only_fields = ('last_login', 'date_joined')
        list_exclude = ('social_auth',)
