from .base.serializers import *  # NOQA
from .annotate.serializers import *  # NOQA
from .identify.serializers import *  # NOQA
from .locate.serializers import *  # NOQA
from .mark.serializers import *  # NOQA
from .relate.serializers import *  # NOQA


class IdentifiedLocatedModelSerializer(
        IdentifiedModelSerializer, LocatedModelSerializer):
    pass


class IdentifiedMarkedModelSerializer(
        IdentifiedModelSerializer, MarkedModelSerializer):
    class Meta:
        list_exclude = (
            'identifiers',
            'markdown',
        )


class IdentifiedRelatedModelSerializer(
        IdentifiedModelSerializer, RelatedModelSerializer):
    class Meta:
        list_exclude = (
            'identifiers',
            'relationships',
            'inverserelationships',
        )
