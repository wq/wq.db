from wq.db.patterns import serializers as patterns

from .models import (
    CustomAttachment, CustomTypedAttachment,
    Entity, Value
    )


class CustomAttachmentSerializer(patterns.AttachmentSerializer):
    class Meta(patterns.AttachmentSerializer.Meta):
        model = CustomAttachment
        exclude = ['parent']

        object_field = 'parent'


class CustomPatternSerializer(patterns.AttachedModelSerializer):
    attachments = CustomAttachmentSerializer(many=True)


class CustomTypedAttachmentSerializer(patterns.TypedAttachmentSerializer):
    class Meta(patterns.TypedAttachmentSerializer.Meta):
        model = CustomTypedAttachment
        exclude = ['parent']

        object_field = 'parent'


class CustomTypedPatternSerializer(patterns.AttachedModelSerializer):
    attachments = CustomTypedAttachmentSerializer(many=True)


class ValueSerializerBase(patterns.TypedAttachmentSerializer):
    class Meta(patterns.TypedAttachmentSerializer.Meta):
        model = Value
        exclude = ('entity',)
        object_field = 'entity'
        type_field = 'attribute'
        type_filter = {}


class ValueSerializerCampaignID(ValueSerializerBase):
    class Meta(ValueSerializerBase.Meta):
        type_filter = {'campaign_id': '{{campaign_id}}'}


class ValueSerializerIsActiveT(ValueSerializerBase):
    class Meta(ValueSerializerBase.Meta):
        type_filter = {'is_active': '1'}


class ValueSerializerIsActiveF(ValueSerializerBase):
    class Meta(ValueSerializerBase.Meta):
        type_filter = {'is_active': '0'}


class ValueSerializerIsActiveTCampaignID(ValueSerializerBase):
    class Meta(ValueSerializerBase.Meta):
        type_filter = {'is_active': '1', 'campaign_id': '{{campaign_id}}'}


class ValueSerializerCategoryDim(ValueSerializerBase):
    class Meta(ValueSerializerBase.Meta):
        type_filter = {'category': 'dimension'}


class ValueSerializerCategoryEmpty(ValueSerializerBase):
    class Meta(ValueSerializerBase.Meta):
        type_filter = {'category': ''}


class ValueSerializerCategoryCtxt(ValueSerializerBase):
    class Meta(ValueSerializerBase.Meta):
        type_filter = {'category': '{{category}}'}


class EntitySerializerBase(patterns.AttachedModelSerializer):
    values = ValueSerializerBase(many=True)

    class Meta:
        model = Entity
        fields = '__all__'


class EntitySerializerCampaignID(EntitySerializerBase):
    values = ValueSerializerCampaignID(many=True)

    class Meta(EntitySerializerBase.Meta):
        pass


class EntitySerializerIsActiveT(EntitySerializerBase):
    values = ValueSerializerIsActiveT(many=True)

    class Meta(EntitySerializerBase.Meta):
        pass


class EntitySerializerIsActiveF(EntitySerializerBase):
    values = ValueSerializerIsActiveF(many=True)

    class Meta(EntitySerializerBase.Meta):
        pass


class EntitySerializerActiveTCampaignID(EntitySerializerBase):
    values = ValueSerializerIsActiveTCampaignID(many=True)

    class Meta(EntitySerializerBase.Meta):
        pass


class EntitySerializerCategoryDim(EntitySerializerBase):
    values = ValueSerializerCategoryDim(many=True)

    class Meta(EntitySerializerBase.Meta):
        pass


class EntitySerializerCategoryEmpty(EntitySerializerBase):
    values = ValueSerializerCategoryEmpty(many=True)

    class Meta(EntitySerializerBase.Meta):
        pass


class EntitySerializerCategoryCtxt(EntitySerializerBase):
    values = ValueSerializerCategoryCtxt(many=True)

    class Meta(EntitySerializerBase.Meta):
        pass
