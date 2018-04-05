from wq.db.rest.serializers import ModelSerializer


class UserSerializer(ModelSerializer):
    class Meta:
        exclude = ('id', 'password', 'user_permissions', 'groups',)
        read_only_fields = ('last_login', 'date_joined')
