from .base.serializers import *  # NOQA
from .annotate.serializers import *  # NOQA
from .identify.serializers import *  # NOQA
from .locate.serializers import *  # NOQA
from .mark.serializers import *  # NOQA
from .relate.serializers import *  # NOQA


class IdentifiedAnnotatedModelSerializer(
        IdentifiedModelSerializer, AnnotatedModelSerializer):
    class Meta:
        wq_config = {
            'identified': True,
            'annotated': True,
            'lookup': 'slug',
        }


class IdentifiedLocatedModelSerializer(
        IdentifiedModelSerializer, LocatedModelSerializer):
    class Meta:
        wq_config = {
            'identified': True,
            'located': True,
            'map': True,
            'lookup': 'slug',
        }


class IdentifiedMarkedModelSerializer(
        IdentifiedModelSerializer, MarkedModelSerializer):
    class Meta:
        wq_config = {
            'identified': True,
            'marked': True,
            'lookup': 'slug',
        }


class IdentifiedRelatedModelSerializer(
        IdentifiedModelSerializer, RelatedModelSerializer):
    class Meta:
        wq_config = {
            'identified': True,
            'related': True,
            'lookup': 'slug',
        }
