from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from wq.db.patterns.base import serializers as base
from .models import Identifier


class IdentifierListSerializer(base.TypedAttachmentListSerializer):
    def to_internal_value(self, data):
        data = super(IdentifierListSerializer, self).to_internal_value(data)
        primary = [
            ident for ident in data
            if ident and ident.get('is_primary', None)
        ]
        if not any(primary) and len(data) > 0:
            for ident in data:
                if ident:
                    ident['is_primary'] = True
                    break
        return data


class IdentifierSerializer(base.TypedAttachmentSerializer):
    url = serializers.ReadOnlyField()

    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Identifier
        list_serializer_class = IdentifierListSerializer

        # patterns-specific
        type_field = 'authority_id'


class IdentifiedModelValidator(UniqueTogetherValidator):
    def enforce_required_fields(self, attrs):
        pass

    def filter_queryset(self, attrs, queryset):
        for field in self.fields:
            attrs.setdefault(field, None)
        return super(IdentifiedModelValidator, self).filter_queryset(
            attrs, queryset
        )


class IdentifiedModelSerializer(base.AttachedModelSerializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(required=False)
    identifiers = IdentifierSerializer(many=True)

    def get_unique_together_validators(self):
        return [IdentifiedModelValidator(
            queryset=self.Meta.model.objects.all(),
            fields=['slug']
        )]

    def save(self, *args, **kwargs):
        super(IdentifiedModelSerializer, self).save(*args, **kwargs)
        # Fetch instance from DB in case identifier changed slug while saving
        self.instance = self.Meta.model.objects.get(pk=self.instance.pk)
        return self.instance

    class Meta:
        wq_config = {
            'lookup': 'slug',
        }
