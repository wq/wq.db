from wq.db.rest.models import MultiQuerySet
from wq.db.patterns.models import Identifier
import swapper

if swapper.is_swapped('annotate', 'Annotation'):
    Annotation = None
else:
    Annotation = swapper.load_model('annotate', 'Annotation')


def search(query, auto=True, content_type=None):
    if content_type:
        ctfilter = {'content_type__model': content_type}
    else:
        ctfilter = {}

    # First check for exact identifier matches
    id_matches = Identifier.objects.filter_by_identifier(query)
    id_matches = id_matches.filter(**ctfilter)
    # If "auto" mode and only one distinct object, return first identifier
    if id_matches.distinct('content_type', 'object_id').count() == 1 and auto:
        return id_matches[0:1]

    # Otherwise, include any identifiers containing the case-insensitive string
    id_matches = id_matches | Identifier.objects.filter(
        name__icontains=query
    ).filter(**ctfilter)
    id_matches = id_matches.distinct('content_type', 'object_id')

    # Then, include any annotations containing the string (case insensitive)
    results = [id_matches]
    if Annotation:
        annot_matches = Annotation.objects.filter(
            value__icontains=query
        ).filter(**ctfilter)

        if content_type:
            # If (and only if) content type filter is specified, we can also
            # guarantee that annot_matches won't contain objects already found
            # in id_matches
            annot_matches = annot_matches.exclude(
                object_id__in=id_matches.values_list('object_id', flat=True)
            )
        results.append(annot_matches)

    return MultiQuerySet(*results)
