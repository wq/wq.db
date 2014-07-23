from django.contrib import admin
from .models import File, FileType
from wq.db.patterns.admin import (
    AnnotationInline, RelationshipInline, InverseRelationshipInline
)


class FileAdmin(admin.ModelAdmin):
    inlines = [AnnotationInline, RelationshipInline, InverseRelationshipInline]
    list_display = ('__str__', 'type')
    list_filter = ('type', )

admin.site.register(File, FileAdmin)
admin.site.register(FileType)
