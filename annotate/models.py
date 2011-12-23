from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib import admin

class AnnotatedModel(models.Model):
    annotations = generic.GenericRelation('Annotation')
    class Meta:
        abstract = True

class AnnotationType(models.Model):
    name   = models.CharField(max_length=255)
    models = models.ManyToManyField(ContentType)
    def __unicode__(self):
        return self.name

class AnnotationQualifier(models.Model):
    name   = models.CharField(max_length=255)
    types  = models.ManyToManyField(AnnotationType)
    def __unicode__(self):
        return self.name

class Annotation(models.Model):
    type      = models.ForeignKey(AnnotationType)
    value     = models.CharField(max_length=255, blank=True) # FIXME:numbers?
    qualifier = models.ForeignKey(AnnotationQualifier, null=True, blank=True)

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


class AnnotationInline(generic.GenericTabularInline):
    model = Annotation
    extra = 0

class AnnotatedModelAdmin(admin.ModelAdmin):
    inlines = [
        AnnotationInline,
    ]
