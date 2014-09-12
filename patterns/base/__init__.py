from django.contrib.contenttypes.generic import GenericRelation


# Trick rest_framework into serializing these relationships
class SerializableGenericRelation(GenericRelation):
    def __init__(self, *args, **kwargs):
        super(SerializableGenericRelation, self).__init__(*args, **kwargs)
        self.serialize = True

try:
    from south.modelsinspector import add_ignored_fields
    add_ignored_fields(["^wq.db.patterns.base.SerializableGenericRelation"])
except ImportError:
    pass
