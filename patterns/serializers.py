from .annotate.serializers import *  # NOQA
from .identify.serializers import *  # NOQA
from .locate.serializers import *  # NOQA
from .mark.serializers import *  # NOQA
from .relate.serializers import *  # NOQA


class IdentifiedRelatedModelSerializer(
        IdentifiedModelSerializer, RelatedModelSerializer):
    class Meta:
        list_exclude = (
            'identifiers',
            'relationships',
            'inverserelationships',
        )


class IdentifiedMarkedModelSerializer(
        IdentifiedModelSerializer, MarkedModelSerializer):
    class Meta:
        list_exclude = (
            'identifiers',
            'markdown',
        )
