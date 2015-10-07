from .base.models import *  # NOQA
from .annotate.models import *  # NOQA
from .identify.models import *  # NOQA
from .locate.models import *  # NOQA
from .mark.models import *  # NOQA
from .relate.models import *  # NOQA


class IdentifiedLocatedModel(IdentifiedModel, LocatedModel):
    class Meta:
        abstract = True


class IdentifiedMarkedModel(IdentifiedModel, MarkedModel):
    class Meta:
        abstract = True


class IdentifiedRelatedModelManager(
        IdentifiedModelManager, RelatedModelManager):
    pass


class IdentifiedRelatedModel(IdentifiedModel, RelatedModel):
    objects = IdentifiedRelatedModelManager()

    class Meta:
        abstract = True
