from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib import admin
from reversion import VersionAdmin
from wq.identify.models import IdentifiedModel, IdentifiedModelAdmin

class AnnotatedModel(models.Model):
    annotations = generic.GenericRelation('Annotation')
    class Meta:
        abstract = True

class AnnotationType(IdentifiedModel):
    description = models.TextField()
    models      = models.ManyToManyField(ContentType)
    def fallback_identifier(self):
        return self.description

class Annotation(models.Model):
    type   = models.ForeignKey(AnnotationType)
    value  = models.CharField(max_length=255) # FIXME:numbers?

    # Link can contain a pointer to any model
    # FIXME: restrict to models allowed for given type
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    def __unicode__(self):
      return ('%(object)s -> %(annot)s: %(value)s'
              % {
                  'object': self.content_object,
                  'annot':  self.type,
                  'value':  self.value
                })


class AnnotationTypeAdmin(IdentifiedModelAdmin, VersionAdmin):
    pass

class AnnotationInline(generic.GenericTabularInline):
    model = Annotation

class AnnotatedModelAdmin(VersionAdmin):
    inlines = [
        AnnotationInline,
    ]

admin.site.register(AnnotationType, AnnotationTypeAdmin)
