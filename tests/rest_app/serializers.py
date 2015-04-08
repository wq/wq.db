from wq.db.rest.serializers import ModelSerializer
from .models import OneToOneModel, ExtraModel


class RootModelSerializer(ModelSerializer):
    extramodels = ModelSerializer.for_model(ExtraModel)(many=True)
    onetoonemodel = ModelSerializer.for_model(OneToOneModel)()
