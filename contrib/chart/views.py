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

    def get_grouping(self, sets):
        group = self.request.GET.get('group', None)
        if group:
            return group
        elif sets > 20:
            return "year"
        elif sets > 10:
            return "index"
        else:
            return "year-index"

    def transform_dataframe(self, df):
        from pandas import DataFrame
        group = self.get_grouping(len(df.columns))
        if "index" in group:
            # Separate stats for each column in dataset
            groups = {
                col: df[col]
                for col in df.columns
            }
        else:
            # Stats for entire dataset
            df = df.stack().stack().stack()
            df.reset_index(inplace=True)
            df.set_index('date', inplace=True)
            groups = {
                ('value', 'all', 'all', 'all'): df.value
            }

        # Compute stats for each column, potentially grouped by year
        all_stats = []
        for g, series in groups.items():
            v, units, param, site = g
            if "year" in group or "month" in group:
                groupby = "year" if "year" in group else "month"
                dstats = self.compute_boxplots(series, groupby)
                for s in dstats:
                    s['site'] = site
                    s['type'] = param
                    s['units'] = units
            else:
                stats = self.compute_boxplot(series)
                stats['site'] = site
                stats['type'] = param
                stats['units'] = units
                dstats = [stats]
            all_stats += dstats

        df = DataFrame(all_stats)
        if "year" in group:
            index = ['year', 'site', 'type', 'units']
        elif "month" in group:
            index = ['month', 'site', 'type', 'units']
        else:
            index = ['site', 'type', 'units']
        df.sort(index, inplace=True)
        df.set_index(index, inplace=True)
        df = df.unstack().unstack()
        if "year" in group or "month" in group:
            df = df.unstack()
        return df

    def compute_boxplots(self, series, groupby):
        def groups(d):
            return getattr(d, groupby)

        dstats = []
        for name, g in series.groupby(groups).groups.items():
            stats = self.compute_boxplot(series[g])
            stats[groupby] = name
            dstats.append(stats)
        return dstats

    def compute_boxplot(self, series):
        """
        Compute boxplot for given pandas Series.
        NOTE: Requires matplotlib 1.4!
        """
        from matplotlib.cbook import boxplot_stats
        series = series[series.notnull()]
        if len(series.values) == 0:
            return {}
        stats = boxplot_stats(list(series.values))[0]
        stats = {
            self.NAME_MAP.get(key, key): value
            for key, value in stats.items()
        }
        stats['fliers'] = "|".join(map(str, stats['fliers']))
        return stats


class TimeSeriesView(ChartView, TimeSeriesMixin):
    pass


class BoxPlotView(ChartView, BoxPlotMixin):
    pass
