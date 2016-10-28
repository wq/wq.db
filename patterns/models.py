from .annotate.models import (
    AnnotatedModel,
    AnnotationType,
    Annotation,
)
from .base.models import (
    LabelModel,
)
from .file.models import (
    FiledModel,
    FileType,
    File,
)
from .identify.models import (
    IdentifiedModel,
    Authority,
    Identifier,
    IdentifiedModelManager,
)
from .locate.models import (
    LocatedModel,
    Location,
)
from .mark.models import (
    MarkedModel,
    MarkdownType,
    Markdown,
)
from .relate.models import (
    RelatedModel,
    RelationshipType,
    Relationship,
    InverseRelationshipType,
    InverseRelationship,
    RelatedModelManager,
)

__all__ = (
    'AnnotatedModel',
    'AnnotationType',
    'Annotation',

    'LabelModel',

    'FiledModel',
    'FileType',
    'File',

    'IdentifiedModel',
    'Authority',
    'Identifier',

    'LocatedModel',
    'Location',

    'MarkedModel',
    'MarkdownType',
    'Markdown',

    'RelatedModel',
    'RelationshipType',
    'Relationship',
    'InverseRelationshipType',
    'InverseRelationship',

    'IdentifiedAnnotatedModel',
    'IdentifiedLocatedModel',
    'IdentifiedMarkedModel',
    'IdentifiedRelatedModel',
)


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
