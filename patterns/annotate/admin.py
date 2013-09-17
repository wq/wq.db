from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib import admin

from wq.db.patterns.base import swapper
from .models import AnnotatedModel
from .forms import AnnotationForm


class AnnotationInline(generic.GenericTabularInline):
    model = swapper.load_model('annotate', 'Annotation', required=False)
    form = AnnotationForm
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'type':
            ctype = ContentType.objects.get_for_model(self.parent_model)
            AnnotationType = swapper.load_model(
                'annotate', 'AnnotationType', required=False
            )
            if AnnotationType:
                kwargs["queryset"] = AnnotationType.objects.filter(
                    contenttype=ctype
                )
        return super(AnnotationInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


class AnnotatedModelAdmin(admin.ModelAdmin):
    model = AnnotatedModel
    inlines = [
        AnnotationInline,
    ]


class AnnotationTypeAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'contenttype')
    list_filter = ('contenttype',)
