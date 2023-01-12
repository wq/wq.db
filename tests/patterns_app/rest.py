from wq.db import rest
from .models import (
    Campaign,
    Attribute,
    Entity,
    Value,
)

rest.router.register(
    Campaign,
    lookup="slug",
    nested_arrays=Attribute,
    fields="__all__",
)


@rest.register(Attribute, fields="__all__")
class AttributeSerializer(rest.ModelSerializer):
    class Meta:
        wq_field_config = {
            "is_active": {
                "control": {"appearance": "checkbox"},
            },
        }


class ValueSerializer(rest.ModelSerializer):
    class Meta:
        model = Value
        exclude = ("entity",)
        wq_field_config = {
            "attribute": {
                "control": {"appearance": "attribute-label"},
            }
        }


@rest.register(Entity, fields="__all__")
class EntitySerializer(rest.ModelSerializer):
    values = ValueSerializer(
        many=True,
        wq_config={
            "initial": {
                "type_field": "attribute",
                "filter": {
                    "is_active": True,
                    "campaign": "{{campaign_id}}",
                },
            },
        },
    )

    class Meta:
        wq_field_config = {
            "campaign": {
                "control": {"appearance": "campaign-label"},
            }
        }
        wq_fieldsets = {
            "general": {
                "label": "Info",
                "control": {"appearance": "fieldset"},
                "fields": ["name"],
            },
            "values": {
                "label": "Values",
                "control": {"appearance": "eav-fieldset-array"},
            },
        }
