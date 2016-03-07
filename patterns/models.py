from .annotate.models import *  # NOQA
from .file.models import *  # NOQA
from .identify.models import *  # NOQA
from .locate.models import *  # NOQA
from .mark.models import *  # NOQA
from .relate.models import *  # NOQA


class IdentifiedAnnotatedModel(IdentifiedModel, AnnotatedModel):
    class Meta(IdentifiedModel.Meta):
        abstract = True


class IdentifiedLocatedModel(IdentifiedModel, LocatedModel):
    class Meta(IdentifiedModel.Meta):
        abstract = True


class IdentifiedMarkedModel(IdentifiedModel, MarkedModel):
    class Meta(IdentifiedModel.Meta):
        abstract = True


class IdentifiedRelatedModelManager(
        IdentifiedModelManager, RelatedModelManager):
    pass


class IdentifiedRelatedModel(IdentifiedModel, RelatedModel):
    objects = IdentifiedRelatedModelManager()

    class Meta(IdentifiedModel.Meta):
        abstract = True
