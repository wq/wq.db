from wq.db.rest.serializers import ModelSerializer
from wq.db.rest import app
from wq.db.rest.models import get_ct, get_object_id

from .models import Annotation, AnnotationType

class AnnotationSerializer(ModelSerializer):

    def to_native(self, annot):
        data = {'id':                annot.pk,
                'name':              annot.type.name,
                'annotationtype_id': annot.type.pk,
                'value':             annot.value}
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
            # For the value, Use get_object_id insted of annot.object_id, in
            # case the content object is an IdentifiedModel
            idname = get_ct(annot.content_object).identifier + '_id'
            data[idname] = get_object_id(annot.content_object)
        return data

    def from_native(self, data, files):
        # FIXME: assuming that this is being posted together with a (potentially new)
        # parent object, which is why we are not setting content_type or object_id.
        # This assumption means posting directly to /annotations will not work.
        return super(AnnotationSerializer, self).from_native({
            'id':    data.get('id', None),
            'type':  data['annotationtype_id'],
            'value': data['value'],
        }, files)

    def field_from_native(self, data, files, field_name, into):
        # Handle annotations that are submitted together with their parent object

        # Ideal case: an array of dicts, this can be handled by the default 
        # implementation
        if field_name in data:
            return super(AnnotationSerializer, self).field_from_native(data, files, field_name, into) 

        # Common case: form submission.  In this case the annotation should
        # should be submitted as form fields with the syntax annotation_[typeid]
        # e.g. annotation_23=30.5 will become {'annotationtype_id': 23, 'value': '30.5'}

        # Limit to annotation types valid for this model
        ct = get_ct(self.parent.opts.model)
        atypes = AnnotationType.objects.filter(contenttype=ct)

        # Retrieve form values into more reasonable array/dict format
        annots = []
        for at in atypes:
            fname = 'annotation-%s' % at.pk
            if fname not in data:
                continue
            for val in data.getlist(fname):
                annots.append({
                    'annotationtype_id': at.pk,
                    'value': val
                })

        # Send modified object to default implementation
        return super(AnnotationSerializer, self).field_from_native(
            {field_name: annots}, files, field_name, into
        ) 

    class Meta:
        # Don't validate these fields (again, assuming new annotations will be
        # saved with their parent object) 
        exclude = ["content_type_id", "object_id", "for"]

app.router.register_serializer(Annotation, AnnotationSerializer)
