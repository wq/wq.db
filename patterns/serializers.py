from .base.serializers import (
    AttachmentSerializer,
    TypedAttachmentSerializer,
    AttachedModelSerializer,
)

from .annotate.serializers import AnnotatedModelSerializer
from .file.serializers import FiledModelSerializer
from .identify.serializers import IdentifiedModelSerializer
from .locate.serializers import LocatedModelSerializer
from .mark.serializers import MarkedModelSerializer
from .relate.serializers import RelatedModelSerializer


__all__ = (
    'AttachmentSerializer',
    'TypedAttachmentSerializer',
    'AttachedModelSerializer',

    'AnnotatedModelSerializer',
    'FiledModelSerializer',
    'IdentifiedModelSerializer',
    'LocatedModelSerializer',
    'MarkedModelSerializer',
    'RelatedModelSerializer',

    'IdentifiedAnnotatedModelSerializer',
    'IdentifiedLocatedModelSerializer',
    'IdentifiedMarkedModelSerializer',
    'IdentifiedRelatedModelSerializer',
)


class IdentifiedAnnotatedModelSerializer(
        IdentifiedModelSerializer, AnnotatedModelSerializer):
    pass


class IdentifiedLocatedModelSerializer(
        IdentifiedModelSerializer, LocatedModelSerializer):
    class Meta:
        wq_config = {
            'map': True,
            'lookup': 'slug',
        }


class IdentifiedMarkedModelSerializer(
        IdentifiedModelSerializer, MarkedModelSerializer):
    pass


class IdentifiedRelatedModelSerializer(
        IdentifiedModelSerializer, RelatedModelSerializer):
    pass
