from rest_framework import serializers
from rest_pandas import PandasSerializer
import swapper
EventResult = swapper.load_model('vera', 'EventResult')


class EventResultSerializer(PandasSerializer):
    date = serializers.Field(source="event_date")
    site = serializers.Field(source="event_site.primary_identifier.slug")
    type = serializers.Field(source="result_type.primary_identifier.slug")
    units = serializers.Field(source="result_type.units")
    value = serializers.Field(source="result_value_numeric")

    def get_index(self, dataframe):
        return ['date', 'site', 'type', 'units']

    def get_dataframe(self, data):
        dataframe = super(EventResultSerializer, self).get_dataframe(data)
        return (
            dataframe.unstack().unstack().unstack()
            .dropna(axis=0, how='all')
            .dropna(axis=1, how='all')
        )

    class Meta:
        model = EventResult
        fields = ('date', 'site', 'type', 'units', 'value')
