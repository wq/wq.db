from rest_framework.serializers import Serializer
from wq.db.rest.models import get_ct, ContentType, get_object_id


class SearchResultSerializer(Serializer):
    def to_native(self, obj):
        if hasattr(obj, 'content_type_id') and hasattr(obj, 'content_object'):
            ctype = ContentType.objects.get(pk=obj.content_type_id)
            obj = obj.content_object
        else:
            ctype = get_ct(obj)

        url = ctype.urlbase
        if url:
            url += '/'
        url += str(get_object_id(obj))

        return {
            'url': url,
            'type': str(ctype),
            'label': str(obj)
        }
