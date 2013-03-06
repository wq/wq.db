from django.contrib import admin
from wq.db.files.models import File, FileType
from wq.db.annotate.admin import AnnotationInline
from wq.db.relate.admin import RelationshipInline, InverseRelationshipInline

class FileAdmin(admin.ModelAdmin):
    inlines = [ AnnotationInline, RelationshipInline, InverseRelationshipInline ]
    list_display = ('__unicode__', 'type')
    list_filter  = ('type', )
