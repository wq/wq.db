from rest_framework import serializers
from rest_pandas import PandasSerializer
from wq.db.rest.serializers import LocalDateTimeField
from django.db.models.fields import DateTimeField, FieldDoesNotExist


class ChartSerializer(PandasSerializer):
    index_none_value = "-"

    key_fields = ["series", "date"]
    parameter_fields = ["parameter", "units"]
    value_field = "value"

    @property
    def key_lookups(self):
        return self.key_fields

    @property
    def parameter_lookups(self):
        return self.parameter_fields

    @property
    def value_lookup(self):
        return self.value_field

    @property
    def key_model(self):
        return self.opts.model

    def get_default_fields(self):
        fields = {
            self.value_field: serializers.Field(self.value_lookup),
        }

        for key, lookup in zip(self.parameter_fields, self.parameter_lookups):
            fields[key] = serializers.Field(lookup)

        for key, lookup in zip(self.key_fields, self.key_lookups):
            try:
                field = self.key_model._meta.get_field_by_name(key)[0]
            except FieldDoesNotExist:
                field = None
            if isinstance(field, DateTimeField):
                fields[key] = LocalDateTimeField(lookup)
            else:
                fields[key] = serializers.Field(lookup)

        return fields

    def get_index(self, dataframe):
        """
        By default, all key fields need to be included or pivoting may break
        due to non-unique values.  Move first item in index (which would
        usually be the most important key) to the end to facilitate unstacking.
        """
        index_fields = []
        for key in self.key_fields:
            if key not in self.opts.exclude:
                index_fields.append(key)

        return index_fields[1:] + [index_fields[0]] + self.parameter_fields

    def get_dataframe(self, data):
        """
        Unstack the dataframe so parameter fields and most important key field
        are columns.
        """
        dataframe = super(ChartSerializer, self).get_dataframe(data)
        dataframe.columns.name = ""

        for i in range(len(self.parameter_fields) + 1):
            dataframe = dataframe.unstack()
        dataframe = (
            dataframe
            .dropna(axis=0, how='all')
            .dropna(axis=1, how='all')
        )
        return dataframe
