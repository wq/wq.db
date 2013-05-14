from django.contrib.contenttypes.generic import GenericRelation

class SerializableGenericRelation(GenericRelation):
    def __init__(self, *args, **kwargs):
        super(SerializableGenericRelation, self).__init__(*args, **kwargs)
        self.serialize = True
