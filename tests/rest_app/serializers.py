from wq.db.patterns.serializers import IdentifiedModelSerializer
from wq.db.rest.serializers import ModelSerializer
from .models import OneToOneModel, ExtraModel


class RootModelSerializer(IdentifiedModelSerializer):
    extramodels = ModelSerializer.for_model(ExtraModel)(many=True)
    onetoonemodel = ModelSerializer.for_model(OneToOneModel)()
