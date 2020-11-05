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
        """
        Returns the label for a label

        Args:
            self: (todo): write your description
            instance: (todo): write your description
        """
        return instance.choice.upper()

    class Meta:
        model = ChoiceModel
        fields = "__all__"


class DateLabelSerializer(ModelSerializer):
    date_label = serializers.SerializerMethodField()

    def get_date_label(self, instance):
        """
        Returns the label of the instance.

        Args:
            self: (todo): write your description
            instance: (str): write your description
        """
        return instance.date.strftime('%B %-d, %Y')

    class Meta:
        model = DateModel
        fields = "__all__"


class ItemLabelSerializer(ModelSerializer):
    label = serializers.SerializerMethodField()
    type_id = serializers.SerializerMethodField()
    type_label = serializers.SerializerMethodField()

    def get_label(self, instance):
        """
        Returns label for instance.

        Args:
            self: (todo): write your description
            instance: (todo): write your description
        """
        return '%s: %s' % (instance.type.name, instance.name)

    def get_type_id(self, instance):
        """
        Returns the type id of an instance.

        Args:
            self: (todo): write your description
            instance: (todo): write your description
        """
        return 'id-%s' % instance.type_id

    def get_type_label(self, instance):
        """
        Returns the label of an instance

        Args:
            self: (todo): write your description
            instance: (todo): write your description
        """
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
