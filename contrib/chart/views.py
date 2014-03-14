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
        id_map, unresolved = Identifier.objects.resolve(
            slugs, exclude_apps=['dbio']
        )
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
    """
    For use with chart.timeSeries() in wq/chart.js
    """

    def transform_dataframe(self, df):
        """
        The dataframe is already in a timeseries format.
        """
        return df


class ScatterMixin(object):
    """
    For use with chart.scatter() in wq/chart.js
    """

    def transform_dataframe(self, df):
        """
        Transform timeseries dataframe into a format suitable for plotting two
        values against each other.
        """

        # Only use primary 'value' column, ignoring any other result fields
        # that may have been added to a serializer subclass.
        for key in df.columns.levels[0]:
            if key != 'value':
                df = df.drop(key, axis=1)

        # Remove all indexes/columns except for parameter (which will become
        # the new 'value' field) and site (to allow distinguishing between
        # scatterplot data for each site).
        for name in df.columns.names:
            if name not in ("parameter", "site"):
                df.columns = df.columns.droplevel(name)

        # Rename columns ('value'/parameter column should be nameless)
        df.columns.names = ["", "site"]

        # Only include dates that have data for all parameters
        df = df.dropna(axis=0, how='any')
        return df


class BoxPlotMixin(object):
    """
    For use with chart.boxplot() in wq/chart.js
    """

    NAME_MAP = {
        'q1': 'p25',
        'q3': 'p75',
        'med': 'median',
        'whishi': 'max',
        'whislo': 'min',
    }

    def transform_dataframe(self, df):
        """
        Use matplotlib to compute boxplot statistics on timeseries data.
        """
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
            index = self.get_serializer().get_index(df)
            df.set_index(index[0], inplace=True)
            groups = {
                ('value', 'all', 'all', 'all'): df.value
            }

        # Compute stats for each column, potentially grouped by year
        all_stats = []
        for g, series in groups.items():
            if g[0] != 'value':
                continue
            v, units, param, site = g
            if "year" in group or "month" in group:
                groupby = "year" if "year" in group else "month"
                dstats = self.compute_boxplots(series, groupby)
                for s in dstats:
                    s['site'] = site
                    s['parameter'] = param
                    s['units'] = units
            else:
                stats = self.compute_boxplot(series)
                stats['site'] = site
                stats['parameter'] = param
                stats['units'] = units
                dstats = [stats]
            all_stats += dstats

        df = DataFrame(all_stats)
        if "year" in group:
            index = ['year', 'site', 'parameter', 'units']
        elif "month" in group:
            index = ['month', 'site', 'parameter', 'units']
        else:
            index = ['site', 'parameter', 'units']
        df.sort(index, inplace=True)
        df.set_index(index, inplace=True)
        df.columns.name = ""
        df = df.unstack().unstack()
        if "year" in group or "month" in group:
            df = df.unstack()
        return df

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

    def compute_boxplots(self, series, groupby):
        def groups(d):
            if isinstance(d, tuple):
                d = d[0]
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
        stats['count'] = len(series.values)
        stats['fliers'] = "|".join(map(str, stats['fliers']))
        return stats


class TimeSeriesView(ChartView, TimeSeriesMixin):
    pass


class ScatterView(ChartView, ScatterMixin):
    pass


class BoxPlotView(ChartView, BoxPlotMixin):
    pass
