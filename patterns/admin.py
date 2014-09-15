from django.contrib.admin import *
from .annotate.admin import *
from .identify.admin import *
from .locate.admin import *
from .mark.admin import *
from .relate.admin import *

from .models import IdentifiedRelatedModel, IdentifiedMarkedModel


class IdentifiedRelatedModelAdmin(IdentifiedModelAdmin, RelatedModelAdmin):
    model = IdentifiedRelatedModel
    inlines = [
        IdentifierInline,
        RelationshipInline,
        InverseRelationshipInline
    ]


class IdentifiedMarkedModelAdmin(IdentifiedModelAdmin, MarkedModelAdmin):
    model = IdentifiedRelatedModel
    inlines = [
        IdentifierInline,
        MarkdownInline,
    ]
