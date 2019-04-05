from rest_framework import serializers
from wq.db.rest.serializers import ModelSerializer
from .models import (
    OneToOneModel, ExtraModel, Child, ChoiceModel, DateModel, Item,
    ExpensiveModel,
)


class RootModelSerializer(ModelSerializer):
    extramodels = ModelSerializer.for_model(
        ExtraModel, include_fields="__all__"
    )(many=True)
    onetoonemodel = ModelSerializer.for_model(
        OneToOneModel, include_fields="__all__"
    )()


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


class SlugRefChildSerializer(ModelSerializer):
    class Meta:
        wq_field_config = {
            'parent': {
                 'filter': {
                     'ref_id': 'test'
                 }
            }
        }


class ChoiceLabelSerializer(ModelSerializer):
    choice_label = serializers.SerializerMethodField()

    def get_choice_label(self, instance):
        return instance.choice.upper()

    class Meta:
        model = ChoiceModel
        fields = "__all__"


class DateLabelSerializer(ModelSerializer):
    date_label = serializers.SerializerMethodField()

    def get_date_label(self, instance):
        return instance.date.strftime('%B %-d, %Y')

    class Meta:
        model = DateModel
        fields = "__all__"


class ItemLabelSerializer(ModelSerializer):
    label = serializers.SerializerMethodField()
    type_id = serializers.SerializerMethodField()
    type_label = serializers.SerializerMethodField()

    def get_label(self, instance):
        return '%s: %s' % (instance.type.name, instance.name)

    def get_type_id(self, instance):
        return 'id-%s' % instance.type_id

    def get_type_label(self, instance):
        return instance.type.name.upper()

    class Meta:
        model = Item
        fields = "__all__"


class ExpensiveSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        list_exclude = ('expensive', 'more_expensive')
        config_exclude = ('more_expensive',)
        model = ExpensiveModel
