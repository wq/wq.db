from rest_pandas import PandasView
from wq.db.patterns.models import Identifier
from .serializers import EventResultSerializer
import swapper
EventResult = swapper.load_model('vera', 'EventResult')


class ChartView(PandasView):
    model = EventResult
    serializer_class = EventResultSerializer
    ignore_extra = True

    def get_queryset(self):
        qs = super(ChartView, self).get_queryset()
        qs = qs.select_related('event_site', 'result_type')
        return qs

    @property
    def filter_options(self):
        if hasattr(self, '_filter_options'):
            return self._filter_options

        slugs = self.kwargs['ids'].split('/')
        id_map, unresolved = Identifier.objects.resolve(*slugs)
        options = {}
        if unresolved:
            options['extra'] = []
            for key, items in unresolved.items():
                if len(items) > 0:
                    raise Exception(
                        "Could not resolve %s to a single item!" % key
                    )
                options['extra'].append(key)

        if id_map:
            for slug, ident in id_map.items():
                ctype = ident.content_type.model
                if ctype not in options:
                    options[ctype] = []
                options[ctype].append(ident)

        self._filter_options = options
        return options

    def filter_queryset(self, qs):
        for name, idents in self.filter_options.items():
            if name == "extra":
                continue
            fn = getattr(self, 'filter_by_%s' % name, None)
            ids = [ident.object_id for ident in idents]
            if fn:
                qs = fn(qs, ids)
            else:
                raise Exception("Don't know how to filter by %s" % name)
        if 'extra' in self.filter_options:
            qs = self.filter_by_extra(qs, self.filter_options['extra'])
        return qs

    def filter_by_site(self, qs, ids):
        return qs.filter(event_site__in=ids)

    def filter_by_parameter(self, qs, ids):
        return qs.filter(result_type__in=ids)

    def filter_by_extra(self, qs, extra):
        if self.ignore_extra:
            return qs
        else:
            raise Exception("Extra URL options found: %s" % extra)


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
