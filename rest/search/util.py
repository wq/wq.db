from wq.db.rest.models import MultiQuerySet
from wq.db.patterns.models import Identifier
from wq.db.patterns.base import swapper

if swapper.is_swapped('annotate', 'Annotation'):
    Annotation = None
else:
    Annotation = swapper.load_model('annotate', 'Annotation')


def search(query, auto=True):

    id_matches = Identifier.objects.filter_by_identifier(query)
    if id_matches.count() == 1 and auto:
        return id_matches

    id_like_matches = Identifier.objects.filter(
        name__icontains=query
    ).exclude(
        id__in=id_matches.values_list('id', flat=True)
    )
    if Annotation:
        annot_like_matches = Annotation.objects.filter(value__icontains=query)
        results = [id_matches, id_like_matches, annot_like_matches]
    else:
        results = [id_matches, id_like_matches]

    return MultiQuerySet(*results)
