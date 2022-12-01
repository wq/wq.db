from rest_framework import serializers
from wq.db.rest.serializers import ModelSerializer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})


class UserSerializer(ModelSerializer):
    class Meta:
        exclude = (
            "id",
            "password",
            "user_permissions",
            "groups",
        )
        read_only_fields = ("last_login", "date_joined")
