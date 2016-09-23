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


class ItemSerializer(ModelSerializer):
    class Meta:
        wq_field_config = {
            'type': {
                 'filter': {
                     'active': [
                         '1',

                         # Allow inactive types when editing existing items
                         '{{#id}}0{{/id}}{{^id}}1{{/id}}',
                     ]
                 }
            }
        }
