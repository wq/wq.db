from .annotate.admin import *  # NOQA
from .identify.admin import *  # NOQA
from .locate.admin import *  # NOQA
from .mark.admin import *  # NOQA
from .relate.admin import *  # NOQA

from .models import IdentifiedRelatedModel, IdentifiedMarkedModel


class IdentifiedRelatedModelAdmin(IdentifiedModelAdmin, RelatedModelAdmin):
    model = IdentifiedRelatedModel
    inlines = [
        IdentifierInline,
        RelationshipInline,
        InverseRelationshipInline
    ]


class IdentifiedMarkedModelAdmin(IdentifiedModelAdmin, MarkedModelAdmin):
    model = IdentifiedMarkedModel
    inlines = [
        IdentifierInline,
        MarkdownInline,
    ]
