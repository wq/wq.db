from django.contrib.admin import *
from .annotate.admin import *
from .identify.admin import *
from .locate.admin import *
from .relate.admin import *

from .models import IdentifiedRelatedModel


class IdentifiedRelatedModelAdmin(IdentifiedModelAdmin, RelatedModelAdmin):
    model = IdentifiedRelatedModel
    inlines = [
        IdentifierInline,
        RelationshipInline,
        InverseRelationshipInline
    ]
