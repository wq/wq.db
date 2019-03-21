from rest_framework.generics import ListAPIView
from wq.db.patterns.identify.filters import IdentifierFilterBackend
from .models import FilterableModel
from wq.db.rest.serializers import ModelSerializer


class FilterableView(ListAPIView):
    serializer_class = ModelSerializer.for_model(
        FilterableModel,
        include_fields='__all__',
    )
    filter_backends = [IdentifierFilterBackend]
    queryset = FilterableModel.objects.all()

    router = None
    action = None

    def filter_by_identifiedmodel(self, queryset, ids):
        return queryset.filter(
            parent_id__in=ids,
        )
