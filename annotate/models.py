from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib import admin

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

class AnnotationManager(models.Manager):
    # Default implementation of get_or_create doesn't work well with generics
    def get_or_create(self, **kwargs):
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            return self.create(**kwargs), True

class Annotation(models.Model):
    type      = models.ForeignKey(AnnotationType)
    value     = models.CharField(max_length=255, null=True, blank=True) # FIXME:numbers?
    qualifier = models.ForeignKey(AnnotationQualifier, null=True, blank=True)

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

class AnnotationSet(generic.GenericRelation):
    def __init__(self, *args, **kwargs):
       if len(args) == 0:
           args = ['Annotation'] 
       kwargs['related_name'] = None
       super(AnnotationSet, self).__init__(*args, **kwargs)

class AnnotatedModel(models.Model):
    annotations = AnnotationSet()
    class Meta:
        abstract = True

class AnnotationInline(generic.GenericTabularInline):
    model = Annotation
    extra = 0

class AnnotatedModelAdmin(admin.ModelAdmin):
    inlines = [
        AnnotationInline,
    ]
