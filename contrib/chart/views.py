from rest_pandas import PandasView
from wq.db.patterns.models import Identifier
from .serializers import EventResultSerializer
import swapper
EventResult = swapper.load_model('vera', 'EventResult')


class ChartView(PandasView):
    model = EventResult
    serializer_class = EventResultSerializer

    def get_queryset(self):
        qs = super(ChartView, self).get_queryset()
        qs = qs.select_related('event_site', 'result_type')
        return qs

    def filter_queryset(self, qs):
        slugs = self.kwargs['ids'].split('/')
        id_map, unresolved = Identifier.objects.resolve(*slugs)
        extra = []
        if unresolved:
            for key, items in unresolved.items():
                if len(items) > 0:
                    raise Exception(
                        "Could not resolve %s to a single item!" % key
                    )
                extra.append(key)

        idents = {}
        for slug, ident in id_map.items():
            ctype = ident.content_type.model
            if ctype not in idents:
                idents[ctype] = []
            idents[ctype].append(ident.object_id)

        for ctype, ids in idents.items():
            fn = getattr(self, 'filter_by_%s' % ctype, None)
            if fn:
                qs = fn(qs, ids)
            else:
                raise Exception("Don't know how to filter by %s" % ctype)

        if extra:
            qs = self.filter_by_extra(qs, self)
        return qs

    def filter_by_site(self, qs, ids):
        return qs.filter(event_site__in=ids)

    def filter_by_parameter(self, qs, ids):
        return qs.filter(result_type__in=ids)

    def filter_by_extra(self, qs, extra):
        return qs


class TimeSeriesMixin(object):
    def transform_dataframe(self, df):
        return df


class BoxPlotMixin(object):
    NAME_MAP = {
        'q1': 'p25',
        'q3': 'p75',
        'med': 'median',
        'whishi': 'max',
        'whislo': 'min',
    }

    def transform_dataframe(self, df):
        from matplotlib.cbook import boxplot_stats
        from pandas import DataFrame
        s = []
        for name, g in df.groupby(lambda d: d.month):
            stats = boxplot_stats(g)[0]
            stats = {
                self.NAME_MAP.get(key, key): value
                for key, value in stats.items()
            }
            stats['name'] = name
            s.append(stats)
        df = DataFrame(s)
        df.set_index('name', inplace=True)
        return df


class TimeSeriesView(ChartView, TimeSeriesMixin):
    pass


class BoxPlotView(ChartView, BoxPlotMixin):
    pass
