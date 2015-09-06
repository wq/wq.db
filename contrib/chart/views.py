from rest_pandas import (
    PandasView, PandasUnstackedSerializer, PandasScatterSerializer,
    PandasBoxplotSerializer,
)
from wq.db.patterns.identify.filters import IdentifierFilterBackend
from .serializers import ChartModelSerializer


class ChartView(PandasView):
    serializer_class = ChartModelSerializer
    filter_backends = [IdentifierFilterBackend]


class TimeSeriesMixin(object):
    """
    For use with chart.timeSeries() in wq/chart.js
    """
    pandas_serializer_class = PandasUnstackedSerializer


class ScatterMixin(object):
    """
    For use with chart.scatter() in wq/chart.js
    """
    pandas_serializer_class = PandasScatterSerializer


class BoxPlotMixin(object):
    """
    For use with chart.boxplot() in wq/chart.js
    """
    pandas_serializer_class = PandasBoxplotSerializer
