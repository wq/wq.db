from wq.db.contrib.chart import views as chart
from wq.db.contrib.chart.serializers import ChartModelSerializer
from .models import Value


class ValueSerializer(ChartModelSerializer):
    key_lookups = ['series.primary_identifier.slug', 'date']

    class Meta:
        model = Value


class ChartView(chart.ChartView):
    serializer_class = ValueSerializer
    model = Value

    def filter_by_series(self, qs, series):
        return qs.filter(series_id__in=series)

    def filter_by_extra(self, qs, *extra):
        return qs.filter(parameter__in=extra[0])


class TimeSeriesView(ChartView, chart.TimeSeriesMixin):
    pass


class ScatterView(ChartView, chart.ScatterMixin):
    pass


class BoxPlotView(ChartView, chart.BoxPlotMixin):
    pass
