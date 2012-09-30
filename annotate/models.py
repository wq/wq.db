from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib import admin

class AnnotationType(models.Model):
    name        = models.CharField(max_length=255)
    contenttype = models.ForeignKey(ContentType, null=True, blank=True)

    # Assign a value to annotated_model to automatically set contenttype
    # (Useful for subclasses with a single target model)
    annotated_model = None

    def __unicode__(self):
        for f in self._meta.get_all_related_objects():
            # Check for any linked subclasses as they may have a more
            # meaningful representation
            if f.field.__class__ == models.OneToOneField:
                try:
                    child = getattr(self, f.get_accessor_name())
                except f.field.model.DoesNotExist:
                    continue
                else:
                    return unicode(child)
        # Fall back to name
        return self.name

    def clean(self, *args, **kwargs):
        if self.annotated_model is not None:
            self.contenttype = ContentType.objects.get_for_model(self.annotated_model)

    class Meta:
        db_table = 'wq_annotationtype'
            
class AnnotationManager(models.Manager):

    # Collapse annotations into dict for simple access
    @property
    def vals(self):
        if (hasattr(self, '_vals')):
            return getattr(self, '_vals')

        vals = {}
        for annot in self.all():
            vals[str(annot.type)] = annot.value

        setattr(self, '_vals', vals)
        return vals

    # Default implementation of get_or_create doesn't work well with generics
    def get_or_create(self, **kwargs):
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            return self.create(**kwargs), True

class Annotation(models.Model):
    type      = models.ForeignKey(AnnotationType)
    value     = models.TextField(null=True, blank=True)

    # Link can contain a pointer to any model
    # FIXME: restrict to models allowed for given type
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    objects = AnnotationManager()

    def __unicode__(self):
      return ('%(object)s -> %(annot)s: %(value)s'
              % {
                  'object': self.content_object,
                  'annot':  self.type,
                  'value':  self.value
                })

    class Meta:
        db_table = 'wq_annotation'
            
class AnnotationSet(generic.GenericRelation):
    def __init__(self, *args, **kwargs):
       if len(args) == 0:
           kwargs['to'] = "Annotation"
       kwargs['related_name'] = None
       super(AnnotationSet, self).__init__(*args, **kwargs)

class AnnotatedModel(models.Model):
    annotations = AnnotationSet()

    @property
    def vals(self):
        return self.annotations.vals

    class Meta:
        abstract = True

# Tell south not to worry about the "custom" field type
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^wq.db.annotate.models.AnnotationSet"])
