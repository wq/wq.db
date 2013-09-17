from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from wq.db.patterns.base import SerializableGenericRelation, swapper
from django.contrib import admin
from django.core.exceptions import FieldError
from collections import OrderedDict

ANNOTATIONTYPE_MODEL = (
    swapper.is_swapped('annotate', 'AnnotationType') or 'AnnotationType'
)
ANNOTATION_MODEL = swapper.is_swapped('annotate', 'Annotation') or 'Annotation'


class AnnotationTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

    def resolve_names(self, *names):
        resolved = {}
        success = True
        for name in names:
            try:
                resolved[name] = self.get_by_natural_key(name)
            except self.model.DoesNotExist:
                success = False
                resolved[name] = None
        return resolved, success


class BaseAnnotationType(models.Model):
    name = models.CharField(max_length=255)
    contenttype = models.ForeignKey(ContentType, null=True, blank=True)

    # Assign a value to annotated_model to automatically set contenttype
    # (Useful for subclasses with a single target model)
    annotated_model = None

    objects = AnnotationTypeManager()

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

    def natural_key(self):
        return (self.name,)

    def clean(self, *args, **kwargs):
        if self.annotated_model is not None:
            self.contenttype = ContentType.objects.get_for_model(
                self.annotated_model
            )

    class Meta:
        abstract = True


class AnnotationType(BaseAnnotationType):
    class Meta:
        db_table = 'wq_annotationtype'
        swappable = swapper.swappable_setting('annotate', 'AnnotationType')


class AnnotationManager(models.Manager):

    # Collapse annotations into dict for simple access
    @property
    def vals(self):
        if (hasattr(self, '_vals')):
            return getattr(self, '_vals')

        vals = OrderedDict()
        for annot in self.all():
            vals[annot.type.natural_key()[0]] = annot.value

        setattr(self, '_vals', vals)
        return vals

    # Default implementation of get_or_create doesn't work well with generics
    def get_or_create(self, **kwargs):
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            return self.create(**kwargs), True

    # Fix filtering across generic relations
    def filter(self, *args, **kwargs):

        def add_content_type(model):
            ctype = ContentType.objects.get_for_model(model)
            if 'content_type' in kwargs and kwargs['content_type'] != ctype:
                raise FieldError(
                    "Cannot match more than one generic relationship!"
                )
            kwargs['content_type'] = ctype

        for rel in self.model._meta.get_all_related_many_to_many_objects():
            if not isinstance(rel.field, generic.GenericRelation):
                continue
            rname = rel.field.related_query_name()
            for key in kwargs.keys():
                if key == rname or key.startswith(rname + '__'):
                    add_content_type(rel.model)

        return super(AnnotationManager, self).filter(*args, **kwargs)


class BaseAnnotation(models.Model):
    type = models.ForeignKey(ANNOTATIONTYPE_MODEL)

    # Link can contain a pointer to any model
    # FIXME: restrict to models allowed for given type
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = generic.GenericForeignKey()

    objects = AnnotationManager()

    def __unicode__(self):
        return (
            '%(object)s -> %(annot)s: %(value)s'
            % {
                'object': self.content_object,
                'annot': self.type,
                'value': self.value
            })

    class Meta:
        abstract = True


class Annotation(BaseAnnotation):
    value = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'wq_annotation'
        swappable = swapper.swappable_setting('annotate', 'Annotation')


class AnnotationSet(SerializableGenericRelation):
    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            kwargs['to'] = ANNOTATION_MODEL
        kwargs['related_name'] = None
        super(AnnotationSet, self).__init__(*args, **kwargs)


class AnnotatedModel(models.Model):
    annotations = AnnotationSet()

    @property
    def vals(self):
        return self.annotations.vals

    @vals.setter
    def vals(self, vals):
        AnnotationType = swapper.load_model('annotate', 'AnnotationType')
        types, success = AnnotationType.objects.resolve_names(*(vals.keys()))
        if not success:
            missing = [name for name, atype in types.items() if atype is None]
            raise TypeError(
                "Could not identify one or more annotation types: %s!"
                % missing
            )

        for name, atype in types.items():
            annot, is_new = self.annotations.get_or_create(type=atype)
            annot.value = vals[name]
            annot.save()

    class Meta:
        abstract = True

# Tell south not to worry about the "custom" field type
from south.modelsinspector import add_ignored_fields
add_ignored_fields(["^wq.db.patterns.annotate.models.AnnotationSet"])
