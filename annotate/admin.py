from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib import admin

from .models import AnnotationType, Annotation, AnnotatedModel
from .forms  import AnnotationForm

class AnnotationInline(generic.GenericTabularInline):
    model = Annotation
    form  = AnnotationForm
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'type':
            ctype = ContentType.objects.get_for_model(self.parent_model)
            kwargs["queryset"] = AnnotationType.objects.filter(contenttype=ctype)
        return super(AnnotationInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

class AnnotatedModelAdmin(admin.ModelAdmin):
    model = AnnotatedModel
    inlines = [
        AnnotationInline,
    ]

class AnnotationTypeAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'contenttype')
    list_filter = ('contenttype',)
