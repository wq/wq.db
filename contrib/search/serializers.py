from rest_framework.serializers import Serializer
from wq.db.rest.models import get_ct, ContentType, get_object_id
from wq.db.patterns.models import Identifier, Annotation
from django.core.exceptions import ImproperlyConfigured


class SearchResultSerializer(Serializer):
    def to_representation(self, obj):
        if hasattr(obj, 'content_type_id') and hasattr(obj, 'content_object'):
            ctype = ContentType.objects.get(pk=obj.content_type_id)
            if isinstance(obj, Identifier):
                match_str = "%s (%s)" % (obj.name, obj.slug)
            elif isinstance(obj, Annotation):
                match_str = obj.value
            else:
                match_str = str(obj)
            obj = obj.content_object
        else:
            ctype = get_ct(obj)
            match_str = str(obj)
        if not ctype.is_registered():
            raise ImproperlyConfigured(
                "Register %s to include it in search results"
                % ctype.model_class()
            )

        obj_id = get_object_id(obj)

        url = ctype.urlbase
        if url:
            url += '/'
        url += str(obj_id)

        return {
            'id': obj_id,
            'url': url,
            'type': str(ctype),
            'label': str(obj),
            'match': match_str,
        }
