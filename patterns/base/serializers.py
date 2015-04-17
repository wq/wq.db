from wq.db.rest.serializers import ModelSerializer
from rest_framework import serializers
from wq.db.rest.models import get_ct, get_object_id


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
                model.objects.create(**attachment)
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
                    exist = model.objects.get(pk=attachment['id'])
                    for key, val in attachment.items():
                        setattr(exist, key, val)
                    exist.save()
                else:
                    model.objects.create(**attachment)
        return obj

    def extract_attachments(self, validated_data):
        fields = self.get_fields()
        attachment_data = {}
        for name, field in fields.items():
            if isinstance(field, AttachmentListSerializer):
                attachment_data[name] = validated_data.pop(name, [])
        return validated_data, attachment_data

    def set_parent_object(self, attachment, instance, name):
        attachment['content_object'] = instance
