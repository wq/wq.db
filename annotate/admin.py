from django.contrib.contenttypes import generic
from django.contrib import admin

from wq.annotate.models import Annotation, AnnotatedModel

class AnnotationInline(generic.GenericTabularInline):
    model = Annotation
    extra = 0

class AnnotatedModelAdmin(admin.ModelAdmin):
    model = AnnotatedModel
    inlines = [
        AnnotationInline,
    ]

