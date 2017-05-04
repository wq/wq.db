from wq.db.rest.serializers import ModelSerializer
from rest_framework import serializers
from wq.db.rest.models import get_ct, get_object_id
from natural_keys import NaturalKeySerializer, NaturalKeyModelSerializer


class AttachmentListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = super(AttachmentListSerializer, self).to_representation(data)
        if not self.parent:
            return

        wq_config = self.child.get_wq_config()
        initial = wq_config.get('initial', None)
        if initial and not data and self.parent.is_detail:
            if self.parent.instance and not self.parent.instance.pk:
                data = self.default_attachments(initial)

        for i, row in enumerate(data):
            row['@index'] = i
        return data

    def default_attachments(self, initial):
        data = []
        for i in range(0, int(initial)):
            data.append({'new_attachment': True})
        return data


class TypedAttachmentListSerializer(AttachmentListSerializer):
    def get_value(self, dictionary):
        # Handle attachments that are submitted together with their parent
        value = super(TypedAttachmentListSerializer, self).get_value(
            dictionary
        )
        if not isinstance(value, list):
            return []
        for i, row in enumerate(value):
            empty = True
            if isinstance(row, dict):
                for key, val in row.items():
                    if key == self.child.Meta.type_field:
                        continue
                    elif val:
                        empty = False
            if empty:
                value[i] = None
        return value

    def default_attachments(self, initial):
        if not isinstance(initial, dict):
            return super(
                TypedAttachmentListSerializer, self
            ).add_attachments(initial)

        wq_config = self.child.get_wq_config()
        type_field = None
        for field in wq_config['form']:
            if field['name'] == initial.get('type_field'):
                type_field = field.copy()

        if not type_field:
            return []

        if initial.get('filter'):
            type_field['filter'] = initial['filter']
        types = self.child.get_lookup_choices(
            type_field,
            self.context.get('request').GET.dict()
            )

        data = [{
           'new_attachment': True,
           type_field['name'] + '_id': row['id'],
           type_field['name'] + '_label': row['label'],
        } for row in types]

        return data


class AttachmentSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        kwargs['allow_null'] = True
        super(AttachmentSerializer, self).__init__(*args, **kwargs)

    class Meta:
        list_serializer_class = AttachmentListSerializer


class TypedAttachmentSerializer(AttachmentSerializer):
    def to_representation(self, obj):
        data = super(TypedAttachmentSerializer, self).to_representation(obj)

        has_parent = (
            self.parent and self.parent.parent and
            hasattr(self.parent.parent.Meta, 'model')
        )
        if has_parent:
            # This is being serialized with its parent object, don't need to
            # reference the parent again.
            pass
        else:
            # Include pointer to parent object. Collapse content_type and
            # object_id into a single attribute: the identifier for the content
            # type plus '_id' e.g. if contenttype's name is 'visit' then the
            # attribute is 'visit_id'.  This lets us pretend the generic
            # foreign key is a regular one in client.  For the value, Use
            # get_object_id insted of obj.object_id, in case the the content
            # object is an IdentifiedModel

            parent_obj = getattr(obj, self.Meta.object_field)
            if parent_obj is not None:
                idname = get_ct(parent_obj).identifier
                data[idname + '_id'] = get_object_id(parent_obj)

                # In detail views, include full parent object (without _id
                # suffix)
                if self.is_detail:
                    from wq.db import rest
                    data[idname] = rest.router.serialize(parent_obj)
        return data

    def get_wq_config(self):
        config = super(TypedAttachmentSerializer, self).get_wq_config()
        if 'initial' not in config:
            config['initial'] = {
                'type_field': self.Meta.type_field.replace('_id', ''),
                'filter': self.Meta.type_filter,
            }
        return config

    class Meta:
        # Don't validate these fields (items are saved with their parent)
        exclude = ("content_type", "object_id",)
        list_serializer_class = TypedAttachmentListSerializer

        # patterns-specific meta
        type_field = 'type_id'
        type_filter = {}
        object_field = 'content_object'


class AttachedModelSerializer(ModelSerializer):
    def create(self, validated_data):
        model_data, attachment_data = self.extract_attachments(validated_data)
        instance = super(AttachedModelSerializer, self).create(model_data)

        fields = self.get_fields()
        for name in attachment_data:
            model = fields[name].child.Meta.model
            for attachment in attachment_data[name]:
                if not attachment:
                    continue
                self.set_parent_object(attachment, instance, name)
                self.create_attachment(model, attachment, name)
        return instance

    def update(self, instance, validated_data):
        model_data, attachment_data = self.extract_attachments(validated_data)
        obj = super(
            AttachedModelSerializer, self
        ).update(instance, model_data)

        fields = self.get_fields()
        for name in attachment_data:
            model = fields[name].child.Meta.model
            for attachment in attachment_data[name]:
                if not attachment:
                    continue
                self.set_parent_object(attachment, instance, name)
                if 'id' in attachment:
                    exist = self.get_attachment(model, attachment['id'])
                    self.update_attachment(exist, attachment, name)
                else:
                    self.create_attachment(model, attachment, name)
        return obj

    def extract_attachments(self, validated_data):
        fields = self.get_fields()
        attachment_data = {}
        for name, field in fields.items():
            if isinstance(field, AttachmentListSerializer):
                attachment_data[name] = validated_data.pop(name, [])
        return validated_data, attachment_data

    def set_parent_object(self, attachment, instance, name):
        serializer = self.get_fields()[name].child
        fk_name = getattr(serializer.Meta, 'object_field', 'content_object')
        attachment[fk_name] = instance

    def get_attachment(self, model, pk):
        return model.objects.get(pk=pk)

    def update_attachment(self, exist, attachment, name):
        field = self.get_fields()[name]
        attachment.pop('id')
        field.child.update(exist, attachment)

    def create_attachment(self, model, attachment, name):
        field = self.get_fields()[name]
        field.child.create(attachment)


class NaturalKeyModelSerializer(NaturalKeyModelSerializer, ModelSerializer):
    def get_fields(self):
        fields = ModelSerializer.get_fields(self)
        fields.update(self.build_natural_key_fields())
        return fields

    def get_wq_field_info(self, name, field, model=None):
        if isinstance(field, NaturalKeySerializer):
            children = [
                self.get_wq_field_info(n, f, model=field.Meta.model)
                for n, f in field.get_fields().items()
            ]
            if len(children) == 1:
                info = children[0]
                info['name'] = name + '[%s]' % info['name']

                fk = self.get_wq_foreignkey_info(field.Meta.model)
                if fk:
                    info['wq:ForeignKey'] = fk
            else:
                info = {
                    'name': name,
                    'type': 'group',
                    'bind': {'required': True},
                    'children': children
                }
            info['label'] = field.label or name.replace('_', ' ').title()
            return info
        else:
            return super(NaturalKeyModelSerializer, self).get_wq_field_info(
                name, field, model
            )


class NaturalKeyAttachedModelSerializer(NaturalKeyModelSerializer,
                                        AttachedModelSerializer):

    def create(self, validated_data):
        self.convert_natural_keys(
            validated_data
        )
        return AttachedModelSerializer.create(
            self, validated_data
        )
