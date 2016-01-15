from .identify.views import IdentifiedModelViewSet
from .relate.views import RelatedModelViewSet


class IdentifiedRelatedModelViewSet(
        IdentifiedModelViewSet, RelatedModelViewSet):
    pass
