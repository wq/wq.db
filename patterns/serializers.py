from .base.serializers import *  # NOQA
from .annotate.serializers import *  # NOQA
from .file.serializers import *  # NOQA
from .identify.serializers import *  # NOQA
from .locate.serializers import *  # NOQA
from .mark.serializers import *  # NOQA
from .relate.serializers import *  # NOQA


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
