from django.db.models import *
from .base.models import *
from .annotate.models import *
from .identify.models import *
from .locate.models import *
from .relate.models import *


class IdentifiedRelatedModelManager(
        IdentifiedModelManager, RelatedModelManager):
    pass


class IdentifiedRelatedModel(IdentifiedModel, RelatedModel):
    objects = IdentifiedRelatedModelManager()

    class Meta:
        abstract = True
