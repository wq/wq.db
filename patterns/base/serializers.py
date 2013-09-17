from wq.db.rest.serializers import ModelSerializer
from wq.db.rest import app
from wq.db.rest.models import get_ct, get_object_id

from wq.db.patterns.base import swapper


class TypedAttachmentSerializer(ModelSerializer):
    attachment_fields = ['id']
    required_fields = []
    type_model = None
    type_field = 'type'
    object_field = 'content_object'

    def to_native(self, obj):
        data = super(TypedAttachmentSerializer, self).to_native(obj)

        has_parent = self.parent and hasattr(self.parent.opts, 'model')
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
            idname = get_ct(parent_obj).identifier + '_id'
            data[idname] = get_object_id(parent_obj)
        return data

    @property
    def expected_types(self):
        return self.type_model.objects.all()

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

    def field_from_native(self, data, files, field_name, into):
        # Handle attachments that are submitted together with their parent

        # Ideal case: an array of dicts, this can be handled by the default
        # implementation
        if field_name in data:
            return super(TypedAttachmentSerializer, self).field_from_native(
                data, files, field_name, into
            )
        # Common case: form submission.  In this case each attachment should
        # be submitted as form fields with names in the format [model]_[typeid]
        # e.g. annotation_23=30.5 will become {'type': 23, 'value': '30.5'}

        # Retrieve form values into more usable array/dict format
        attachments = []

        ct = get_ct(self.opts.model)
        i = 0
        for atype in self.expected_types:
            fields = {
                afield: '%s-%s-%s' % (
                    ct.identifier,
                    get_object_id(atype) if atype else '',
                    afield
                ) for afield in self.attachment_fields
            }
            found = False
            for key in fields.values():
                if key in data:
                    found = True
            if found:
                attachment = self.create_dict(atype, data, fields, i)
                if attachment:
                    attachments.append(attachment)
                i += 1

        # Send modified object to default implementation
        return super(TypedAttachmentSerializer, self).field_from_native(
            {field_name: attachments}, files, field_name, into
        )

    class Meta:
        # Don't validate these fields (items are saved with their parent)
        exclude = ("content_type", "content_type_id",
                   "object_id", "label", "for")
