from wq.db import resources
from wq.db.util import get_id

from .models import Annotation, AnnotatedModel

class AnnotationResource(resources.ModelResource):
    model = Annotation
    def serialize_model(self, instance):
        return serialize_annotation(instance, True)

class AnnotationContextMixin(resources.ContextMixin):
    model = Annotation
    target_model = AnnotatedModel
    def get_data(self, instance):
        return map(serialize_annotation, instance.annotations.all())

def serialize_annotation(annot, include_pointer=False):
    data = {'id':                annot.pk,
            'name':              annot.type.name,
            'annotationtype_id': annot.type.pk,
            'value':             annot.value}
    if include_pointer:
        idname = get_id(annot.content_type) + '_id'
        data[idname] = annot.object_id
    return data

resources.register(Annotation, AnnotationResource)
resources.register_context_mixin(AnnotationContextMixin)
