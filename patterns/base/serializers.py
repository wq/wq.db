from wq.db.rest.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework.utils import model_meta
from wq.db.rest.models import get_ct, get_object_id
from wq.db.rest import compat as html
from .models import NaturalKeyModel


class AttachmentListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = super(AttachmentListSerializer, self).to_representation(data)
        if self.parent:
            for i, row in enumerate(data):
                row['@index'] = i
        return data


class TypedAttachmentListSerializer(AttachmentListSerializer):
    def get_value(self, dictionary):
        # Handle attachments that are submitted together with their parent

        # Ideal case: an array of dicts; this can be handled by the default
        # implementation.  HTML JSON forms will use this approach.
        if self.field_name in dictionary:
            return super(TypedAttachmentListSerializer, self).get_value(
                dictionary
            )

        # Deprecated/"classic" form style, where each attachment is submitted
        # as form fields with names in the format [model]_[typeid] e.g.
        # annotation_23=30.5 will become {'type': 23, 'value': '30.5'}

        # Retrieve form values into more usable array/dict format
        attachments = []
        ct = get_ct(self.child.Meta.model)
        i = 0
        for atype in self.child.expected_types:
            fields = {
                afield: '%s-%s-%s' % (
                    ct.identifier,
                    get_object_id(atype) if atype else '',
                    afield
                ) for afield in self.child.attachment_fields
            }
            found = False
            for key in fields.values():
                if key in dictionary:
                    found = True
            if found:
                attachment = self.child.create_dict(
                    atype, dictionary, fields, i
                )
                if attachment:
                    attachments.append(attachment)
                i += 1

        # Return extracted values to default implementation
        return attachments


class AttachmentSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)


class TypedAttachmentSerializer(AttachmentSerializer):
    attachment_fields = ['id']
    required_fields = []
    type_model = None
    type_field = 'type_id'
    object_field = 'content_object'

    def create_dict(self, atype, data, fields, index):
        attachment = {
            self.type_field: atype.pk if atype else None,
        }
        for field in fields:
            if fields[field] in data:
                attachment[field] = data[fields[field]]
                if field == 'id' and attachment[field]:
                    attachment[field] = int(attachment[field])
        for field in self.required_fields:
            if not attachment.get(field, None):
                return None
        return attachment

    @property
    def expected_types(self):
        return self.type_model.objects.all()

    def to_representation(self, obj):
        data = super(TypedAttachmentSerializer, self).to_representation(obj)

        has_parent = (
            self.parent and self.parent.parent
            and hasattr(self.parent.parent.Meta, 'model')
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

            parent_obj = getattr(obj, self.object_field)
            idname = get_ct(parent_obj).identifier
            data[idname + '_id'] = get_object_id(parent_obj)

            # In detail views, include full parent object (without _id suffix)
            if self.is_detail:
                from wq.db import rest
                data[idname] = rest.router.serialize(parent_obj)
        return data

    class Meta:
        # Don't validate these fields (items are saved with their parent)
        exclude = ("content_type", "object_id",)
        list_serializer_class = TypedAttachmentListSerializer


class AttachedModelSerializer(ModelSerializer):
    def create(self, validated_data):
        model_data, attachment_data = self.extract_attachments(validated_data)
        instance = super(AttachedModelSerializer, self).create(model_data)

        fields = self.get_fields()
        for name in attachment_data:
            model = fields[name].child.Meta.model
            for attachment in attachment_data[name]:
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
        fk_name = getattr(serializer, 'object_field', 'content_object')
        attachment[fk_name] = instance

    def get_attachment(self, model, pk):
        return model.objects.get(pk=pk)

    def update_attachment(self, exist, attachment, name):
        for key, val in attachment.items():
            if key != 'id':
                setattr(exist, key, val)
        exist.save()

    def create_attachment(self, model, attachment, name):
        return model.objects.create(**attachment)


class NaturalKeyValidator(serializers.UniqueTogetherValidator):
    def set_context(self, serializer):
        self.nested_fields = {
            name: serializer.fields[name]
            for name in self.fields
            if isinstance(serializer.fields[name], NaturalKeySerializer)
        }
        super(NaturalKeyValidator, self).set_context(serializer)

    def filter_queryset(self, attrs, queryset):
        attrs = attrs.copy()
        for field in attrs:
            if field in self.nested_fields:
                assert(isinstance(attrs[field], dict))
                cls = self.nested_fields[field].Meta.model
                result = cls._default_manager.filter(
                    **attrs[field]
                )
                if result.count() == 0:
                    # No existing nested object for these values
                    return queryset.none()
                else:
                    # Existing nested object, use it to validate
                    attrs[field] = result[0].pk

        return super(NaturalKeyValidator, self).filter_queryset(
            attrs, queryset
        )


class NaturalKeySerializer(serializers.ModelSerializer):
    """
    Self-nesting Serializer for NaturalKeyModels
    """
    def build_nested_field(self, field_name, relation_info, nested_depth):
        field_class = NaturalKeySerializer.for_model(
            relation_info.related_model,
            validate_key=False,
        )
        field_kwargs = {}
        return field_class, field_kwargs

    def create(self, validated_data):
        model_class = self.Meta.model
        natural_key_fields = model_class.get_natural_key_fields()
        natural_key = []
        for field in natural_key_fields:
            val = validated_data
            for key in field.split('__'):
                val = val[key]
            natural_key.append(val)
        return model_class.objects.find(*natural_key)

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "Updating an existing natural key is not supported."
        )

    @classmethod
    def for_model(cls, model_class, validate_key=True):
        unique_together = model_class._meta.unique_together[0]

        class Serializer(cls):
            class Meta(cls.Meta):
                model = model_class
                fields = unique_together
                if validate_key:
                    validators = [
                        NaturalKeyValidator(
                            queryset=model_class._default_manager,
                            fields=unique_together,
                        )
                    ]
                else:
                    validators = []
        return Serializer

    @classmethod
    def for_depth(cls, model_class):
        return cls

    def to_internal_value(self, data):
        if html.is_html_input(data):
            data = html.parse_json_form(data)
        result = super(NaturalKeySerializer, self).to_internal_value(data)
        return result

    class Meta:
        depth = 1


class NaturalKeyModelSerializer(AttachedModelSerializer):
    """
    Serializer for models with one or more foreign keys to a NaturalKeyModel
    """
    def build_nested_field(self, field_name, relation_info, nested_depth):
        if issubclass(relation_info.related_model, NaturalKeyModel):
            field_class = NaturalKeySerializer.for_model(
                relation_info.related_model,
                validate_key=False,
            )
            field_kwargs = {}
            if relation_info.model_field.null:
                field_kwargs['required'] = False
            return field_class, field_kwargs

        return super(NaturalKeyModelSerializer, self).build_nested_field(
            field_name, relation_info, nested_depth
        )

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(
            NaturalKeyModelSerializer, self
        ).build_relational_field(
            field_name, relation_info
        )
        if issubclass(relation_info.related_model, NaturalKeyModel):
            field_kwargs.pop('queryset')
            field_kwargs['read_only'] = True
        return field_class, field_kwargs

    def get_fields(self):
        fields = super(NaturalKeyModelSerializer, self).get_fields()
        info = model_meta.get_field_info(self.Meta.model)
        for key in fields:
            if not key.endswith('_id'):
                continue
            field = key[:-3]
            if field in fields or field not in info.relations:
                continue
            relation_info = info.relations[field]
            if not issubclass(relation_info.related_model, NaturalKeyModel):
                continue
            field_class, field_kwargs = self.build_nested_field(
                field, relation_info, 1
            )
            fields[field] = field_class(**field_kwargs)
        return fields

    def create(self, validated_data):
        self.convert_natural_keys(
            validated_data
        )
        return super(NaturalKeyModelSerializer, self).create(
            validated_data
        )

    def update(self, instance, validated_data):
        self.convert_natural_keys(
            validated_data
        )
        return super(NaturalKeyModelSerializer, self).update(
            instance, validated_data
        )

    def convert_natural_keys(self, validated_data):
        fields = self.get_fields()
        for name, field in fields.items():
            if name not in validated_data:
                continue
            if isinstance(field, NaturalKeySerializer):
                validated_data[name] = fields[name].create(
                    validated_data[name]
                )
