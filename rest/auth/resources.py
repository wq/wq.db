from wq.db.rest import resources
from django.contrib.auth.models import User

class UserResource(resources.ModelResource):
    model = User
    def get_fields(self, instance):
        fields = super(UserResource, self).get_fields(instance)
        fields.remove('password')
        return fields

class SocialContextMixin(resources.ContextMixin):
    target_model = User
    name = 'social_auth'

    def get_data(self, instance):
        auth = getattr(instance, 'social_auth', None)
        if not auth or auth.count() == 0:
            return None
        
        return {
            'accounts': [{
                'provider_id':    unicode(a.provider),
                'provider_label': a.provider.title(),
                'id':             a.pk,
                'label':          a.uid,
                'can_disconnect': type(a).allowed_to_disconnect(
                    user = instance,
                    backend_name = a.provider,
                    association_id = a.pk
                )
            } for a in auth.all()]
        }

resources.register(User, UserResource)
resources.register_context_mixin(SocialContextMixin)
