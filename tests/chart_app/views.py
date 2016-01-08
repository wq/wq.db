from rest_framework import serializers
from wq.db.contrib.chart import views as chart
from wq.db.contrib.chart.serializers import ChartModelSerializer
from .models import Value


class ValueSerializer(ChartModelSerializer):
    series = serializers.ReadOnlyField(source="series.slug")

    class Meta(ChartModelSerializer.Meta):
        model = Value
        fields = ['series', 'date', 'parameter', 'units', 'value']


class ChartView(chart.ChartView):
    serializer_class = ValueSerializer
    queryset = Value.objects.all()

    def filter_by_series(self, qs, series):
        return qs.filter(series_id__in=series)

    def filter_by_extra(self, qs, *extra):
        return qs.filter(parameter__in=extra[0])


class TimeSeriesView(chart.TimeSeriesMixin, ChartView):
    pass


class ScatterView(chart.ScatterMixin, ChartView):
    pass


class BoxPlotView(chart.BoxPlotMixin, ChartView):
    pass
