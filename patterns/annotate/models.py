from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from wq.db.patterns.base.models import NaturalKeyModel
from django.core.exceptions import FieldError
from collections import OrderedDict

from django.conf import settings
INSTALLED = ('wq.db.patterns.annotate' in settings.INSTALLED_APPS)


class AnnotationType(NaturalKeyModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    class Meta:
        unique_together = [['name']]
        db_table = 'wq_annotationtype'
        abstract = not INSTALLED


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
            if not isinstance(rel.field, GenericRelation):
                continue
            rname = rel.field.related_query_name()
            for key in kwargs.keys():
                if key == rname or key.startswith(rname + '__'):
                    add_content_type(rel.model)

        return super(AnnotationManager, self).filter(*args, **kwargs)


class Annotation(models.Model):
    type = models.ForeignKey(AnnotationType)
    value = models.TextField(null=True, blank=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey()

    objects = AnnotationManager()

    def __str__(self):
        return (
            '%(object)s -> %(annot)s: %(value)s'
            % {
                'object': self.content_object,
                'annot': self.type,
                'value': self.value
            })

    class Meta:
        db_table = 'wq_annotation'
        abstract = not INSTALLED


class AnnotatedModel(models.Model):
    annotations = GenericRelation(Annotation)

    @property
    def vals(self):
        return self.annotations.vals

    @vals.setter
    def vals(self, vals):
        keys = [(key,) for key in vals.keys()]
        types, success = AnnotationType.objects.resolve_keys(keys)
        if not success:
            missing = [name for name, atype in types.items() if atype is None]
            raise TypeError(
                "Could not identify one or more annotation types: %s!"
                % missing
            )

        for name, atype in types.items():
            annot, is_new = self.annotations.get_or_create(type=atype)
            annot.value = vals[name[0]]
            annot.save()

    class Meta:
        abstract = True
