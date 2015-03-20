from rest_framework.serializers import Serializer
from wq.db.rest.models import get_ct, ContentType, get_object_id


class SearchResultSerializer(Serializer):
    def to_representation(self, obj):
        if hasattr(obj, 'content_type_id') and hasattr(obj, 'content_object'):
            ctype = ContentType.objects.get(pk=obj.content_type_id)
            obj = obj.content_object
        else:
            ctype = get_ct(obj)

        obj_id = get_object_id(obj)

        url = ctype.urlbase
        if url:
            url += '/'
        url += str(obj_id)

        return {
            'id': obj_id,
            'url': url,
            'type': str(ctype),
            'label': str(obj)
        }
