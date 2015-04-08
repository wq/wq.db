from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import Annotation, AnnotatedModel
from .forms import AnnotationForm


class AnnotationInline(GenericTabularInline):
    model = Annotation
    form = AnnotationForm
    extra = 0


class AnnotatedModelAdmin(admin.ModelAdmin):
    model = AnnotatedModel
    inlines = [
        AnnotationInline,
    ]


class AnnotationTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'contenttype')
    list_filter = ('contenttype',)
