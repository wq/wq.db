from wq.db.rest.serializers import ModelSerializer
from .models import OneToOneModel, ExtraModel, Child


class RootModelSerializer(ModelSerializer):
    extramodels = ModelSerializer.for_model(ExtraModel)(many=True)
    onetoonemodel = ModelSerializer.for_model(OneToOneModel)()


class ChildSerializer(ModelSerializer):
    class Meta:
        model = Child
        exclude = ('parent',)


class ParentSerializer(ModelSerializer):
    children = ChildSerializer(many=True)
