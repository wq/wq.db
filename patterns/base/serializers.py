from wq.db.rest.serializers import ModelSerializer
from wq.db.rest import app
from wq.db.rest.models import get_ct, get_object_id

from wq.db.patterns.base import swapper

class TypedAttachmentSerializer(ModelSerializer):
    value_field = 'value'
    type_model = None
    type_field = 'type'

    def to_native(self, obj):
        data = super(TypedAttachmentSerializer, self).to_native(obj)

        has_parent = self.parent and hasattr(self.parent.opts, 'model')
        if has_parent:
            # This is being serialized with its parent object, don't need to reference
            # the parent again.
            pass
        else:
            # Include pointer to parent object. Collapse content_type and object_id
            # into a single attribute: the identifier for the content type plus '_id'
            # e.g. if contenttype's name is 'visit' then the attribute is 'visit_id'.
            # This lets us pretend the generic foreign key is a regular one in client.
            # For the value, Use get_object_id insted of obj.object_id, in case the
            # the content object is an IdentifiedModel
            idname = get_ct(obj.content_object).identifier + '_id'
            data[idname] = get_object_id(obj.content_object)
        return data

    @property
    def expected_types(self):
        return self.type_model.objects.all()

    def get_existing(self, atype, field_name):
        if self.parent.object is None:
            return None

        filt = {}
        if atype:
            filt = {self.type_field: atype.pk}
        else:
            filt = {'%s__isnull' % self.type_field: True}

        existing = getattr(self.parent.object, field_name).filter(**filt)
        if existing.count() > 0:
            return existing[0]
        else:
            return None

    def create_dict(self, atype, val, existing, index):
        return {
            'id': existing.pk if existing else None,
            self.type_field: atype.pk if atype else None,
            self.value_field: val,
        }

    def field_from_native(self, data, files, field_name, into):
        # Handle attachments that are submitted together with their parent object

        # Ideal case: an array of dicts, this can be handled by the default 
        # implementation
        if field_name in data:
            return super(TypedAttachmentSerializer, self).field_from_native(data, files, field_name, into) 
        # Common case: form submission.  In this case each attachment should
        # should be submitted as form fields with names in the format [model]_[typeid]
        # e.g. annotation_23=30.5 will become {'type': 23, 'value': '30.5'}

        # Retrieve form values into more usable array/dict format
        attachments = []

        ct = get_ct(self.opts.model)
        i = 0 
        for atype in self.expected_types:
            fname = '%s-%s' % (ct.identifier, get_object_id(atype) if atype else '')
            if fname not in data:
                continue
            existing = self.get_existing(atype, field_name)
            for val in data.getlist(fname):
                obj = self.create_dict(atype, val, existing, i)
                attachments.append(obj)
                i += 1

        # Send modified object to default implementation
        return super(TypedAttachmentSerializer, self).field_from_native(
            {field_name: attachments}, files, field_name, into
        ) 

    class Meta:
        # Don't validate these fields (items are saved with their parent object)
        exclude = ("content_type_id", "object_id", "label", "for")
