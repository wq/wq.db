from rest_framework import serializers
from rest_pandas import PandasSerializer
from wq.db.rest.serializers import LocalDateTimeField
from django.db.models.fields import DateTimeField, FieldDoesNotExist


class ChartModelSerializer(serializers.ModelSerializer):
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
        return self.Meta.model

    def get_fields(self):
        fields = super(ChartModelSerializer, self).get_fields()
        value_kwargs = {}
        if self.value_field != self.value_lookup:
            value_kwargs['source'] = self.value_lookup
        fields[self.value_field] = serializers.ReadOnlyField(**value_kwargs)

        for key, lookup in zip(self.parameter_fields, self.parameter_lookups):
            param_kwargs = {}
            if key != lookup:
                param_kwargs['source'] = lookup
            fields[key] = serializers.ReadOnlyField(**param_kwargs)

        for key, lookup in zip(self.key_fields, self.key_lookups):
            try:
                field = self.key_model._meta.get_field_by_name(key)[0]
            except FieldDoesNotExist:
                field = None
            key_kwargs = {}
            if key != lookup:
                key_kwargs['source'] = lookup
            if isinstance(field, DateTimeField):
                fields[key] = LocalDateTimeField(**key_kwargs)
            else:
                fields[key] = serializers.ReadOnlyField(**key_kwargs)

        return fields


class ChartPandasSerializer(PandasSerializer):
    index_none_value = "-"

    @property
    def model_serializer(self):
        # Compatibility with ListSerializer and ModelSerializer
        return getattr(self, 'child', self)

    def get_key_fields(self):
        return self.model_serializer.key_fields

    def get_parameter_fields(self):
        return self.model_serializer.parameter_fields

    def get_index(self, dataframe):
        """
        By default, all key fields need to be included or pivoting may break
        due to non-unique values.  Move first item in index (which would
        usually be the most important key) to the end to facilitate unstacking.
        """
        index_fields = []
        meta = getattr(self, 'Meta', object())
        for key in self.get_key_fields():
            if key not in getattr(meta, 'exclude', []):
                index_fields.append(key)

        return (
            index_fields[1:] + [index_fields[0]] + self.get_parameter_fields()
        )

    def get_dataframe(self, data):
        """
        Unstack the dataframe so parameter fields and most important key field
        are columns.
        """
        dataframe = super(ChartPandasSerializer, self).get_dataframe(data)
        dataframe.columns.name = ""

        for i in range(len(self.get_parameter_fields()) + 1):
            dataframe = dataframe.unstack()
        dataframe = (
            dataframe
            .dropna(axis=0, how='all')
            .dropna(axis=1, how='all')
        )
        return dataframe
