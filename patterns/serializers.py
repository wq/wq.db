from .annotate.serializers import *
from .identify.serializers import *
from .locate.serializers import *
from .mark.serializers import *
from .relate.serializers import *


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
