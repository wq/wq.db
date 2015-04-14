from rest_pandas import PandasView
from wq.db.patterns.models import Identifier
from .serializers import ChartModelSerializer, ChartPandasSerializer


class ChartView(PandasView):
    serializer_class = ChartModelSerializer
    pandas_serializer_class = ChartPandasSerializer
    ignore_extra = True
    exclude_apps = []

    @property
    def filter_options(self):
        if hasattr(self, '_filter_options'):
            return self._filter_options

        slugs = self.kwargs['ids'].split('/')
        id_map, unresolved = Identifier.objects.resolve(
            slugs, exclude_apps=self.exclude_apps
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

        serializer = self.get_serializer()
        value_column = serializer.value_field
        series_column = serializer.key_fields[0]
        parameter_column = serializer.parameter_fields[0]

        # Only use primary 'value' column, ignoring any other result fields
        # that may have been added to a serializer subclass.
        for key in df.columns.levels[0]:
            if key != value_column:
                df = df.drop(key, axis=1)

        # Remove all indexes/columns except for parameter (which will become
        # the new 'value' field) and series (to allow distinguishing between
        # scatterplot data for each series).
        for name in df.columns.names:
            if name not in (series_column, parameter_column):
                df.columns = df.columns.droplevel(name)

        # Rename columns ('value'/parameter column should be nameless)
        df.columns.names = ["", series_column]

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
        serializer = self.get_serializer()
        value_col = serializer.value_field
        series_col = serializer.key_fields[0]
        param_cols = serializer.parameter_fields
        ncols = 1 + len(param_cols)

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
            index = serializer.get_index(df)
            df.set_index(index[0], inplace=True)
            groups = {
                (value_col,) + ('all',) * ncols: df.value
            }

        # Compute stats for each column, potentially grouped by year
        all_stats = []
        for g, series in groups.items():
            if g[0] != serializer.value_field:
                continue
            series_info = g[-1]
            param_info = list(reversed(g[1:-1]))
            if "year" in group or "month" in group:
                groupby = "year" if "year" in group else "month"
                dstats = self.compute_boxplots(series, groupby)
                for s in dstats:
                    s[series_col] = series_info
                    for pname, pval in zip(param_cols, param_info):
                        s[pname] = pval
            else:
                stats = self.compute_boxplot(series)
                stats[series_col] = series_info
                for pname, pval in zip(param_cols, param_info):
                    stats[pname] = pval
                dstats = [stats]
            all_stats += dstats

        df = DataFrame(all_stats)
        index = [series_col] + param_cols
        if "year" in group:
            index = ['year'] + index
        elif "month" in group:
            index = ['month'] + index
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
