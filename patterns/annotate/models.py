from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from natural_keys import NaturalKeyModel
from ..base.models import LabelModel
from collections import OrderedDict

from django.conf import settings
INSTALLED = ('wq.db.patterns.annotate' in settings.INSTALLED_APPS)


class AnnotationType(NaturalKeyModel, LabelModel):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
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
