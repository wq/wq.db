from rest_framework import serializers
from rest_pandas import PandasSerializer
import swapper
EventResult = swapper.load_model('vera', 'EventResult')
Event = swapper.load_model('vera', 'Event')
EVENT_INDEX = Event._meta.unique_together[0]


class EmptyField(serializers.Field):
    """
    Convert None to - to avoid breaking Pandas indexes.
    """
    def to_native(self, obj):
        if obj is None:
            return "-"
        return super(EmptyField, self).to_native(obj)


class EventResultSerializer(PandasSerializer):
    parameter = serializers.Field(source="result_type.primary_identifier.slug")
    units = EmptyField(source="result_type.units")
    value = serializers.Field(source="result_value")

    def get_default_fields(self):
        """"
        Map fields in EVENT_INDEX to actual natural key lookup values.
        E.g. the default Event has two natural key fields, assuming
        Site is an IdentifiedModel:
            site -> event_site.primary_identifier.slug
            date -> event_date
        """
        fields = {}
        lookups = Event.get_natural_key_fields()
        for key, lookup in zip(EVENT_INDEX, lookups):
            lookup = lookup.replace('__', '.')
            lookup = lookup.replace(
                "primary_identifiers.", "primary_identifier."
            )
            fields[key] = EmptyField("event_" + lookup)
        return fields

    def get_index(self, dataframe):
        """
        By default, all fields from Event's natural key need to be included or
        pivoting may break due to non-unique values.  Move first item in index
        (which would usually be "site") to the end to facilitate unstacking.
        """
        index_fields = []
        for key in EVENT_INDEX:
            if key not in self.opts.exclude:
                index_fields.append(key)

        return index_fields[1:] + [index_fields[0], 'parameter', 'units']

    def get_dataframe(self, data):
        """
        Unstack the dataframe so units, parameter, and site are columns.
        """
        dataframe = super(EventResultSerializer, self).get_dataframe(data)
        dataframe.columns.name = ""
        dataframe = (
            dataframe
            .unstack().unstack().unstack()
            .dropna(axis=0, how='all')
            .dropna(axis=1, how='all')
        )
        return dataframe

    class Meta:
        model = EventResult
