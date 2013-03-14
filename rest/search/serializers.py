from rest_framework import resources
from wq.db.rest import util
from wq.db.patterns.models import Identifier, Annotation

class SearchResource(resources.Resource):
    def search(self, query, auto=True):

        id_matches = Identifier.objects.filter_by_identifier(query)
        if id_matches.count() == 1 and auto:
            return id_matches

        id_like_matches = Identifier.objects.filter(name__icontains=query)
        annot_like_matches = Annotation.objects.filter(value__icontains=query)

        result = util.MultiQuerySet(id_matches, id_like_matches, annot_like_matches)
        return result

    def serialize_model(self, obj):
        if hasattr(obj, 'content_type') and hasattr(obj, 'content_object'):
            ctype = obj.content_type
            obj = obj.content_object
        else:
            ctype = util.get_ct(obj)
        return {
            'url':   '%s/%s' % (util.geturlbase(ctype),
                                util.get_object_id(obj)),
            'type':  unicode(ctype),
            'label': unicode(obj)
        }
