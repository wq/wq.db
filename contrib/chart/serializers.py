from rest_framework import serializers


class ChartModelSerializer(serializers.ModelSerializer):
    class Meta:
        pandas_index = ["date"]
        pandas_unstacked_header = ["series", "units", "parameter"]

        pandas_scatter_coord = ["units", "parameter"]
        pandas_scatter_header = ["series"]

        pandas_boxplot_group = "series"
        pandas_boxplot_date = "date"
        pandas_boxplot_header = ["units", "parameter"]
