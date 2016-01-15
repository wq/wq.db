from wq.db.patterns.models import Identifier, Annotation


def search(query, auto=True, content_type=None, authority_id=None):
    if content_type:
        ctfilter = {'content_type__model': content_type}
    else:
        ctfilter = {}

    idfilter = ctfilter.copy()
    if authority_id:
        idfilter['authority_id'] = authority_id

    distinct_on = ('content_type__model', 'object_id')
    # First check for exact identifier matches
    id_matches = Identifier.objects.filter_by_identifier(query)
    id_matches = id_matches.filter(**idfilter)
    # If "auto" mode and only one distinct object, return first identifier
    if auto:
        if len(id_matches.order_by(*distinct_on).distinct(*distinct_on)) == 1:
            return id_matches[0:1]

    # Otherwise, include any identifiers containing the case-insensitive string
    id_matches = id_matches | Identifier.objects.filter(
        name__icontains=query,
        **idfilter
    ) | Identifier.objects.filter(
        slug__icontains=query,
        **idfilter
    )

    # Avoid duplicates due to multiple similar ids on the same object
    id_matches = id_matches.order_by(*distinct_on).distinct(*distinct_on)

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


class MultiQuerySet(object):
    querysets = []

    def __init__(self, *args, **kwargs):
        self.querysets = args

    def __getitem__(self, index):
        if isinstance(index, slice):
            multi = True
        else:
            multi = False
            index = slice(index, index + 1)

        result = []
        for qs in self.querysets:
            if index.start < qs.count():
                result.extend(qs[index])
            index = slice(index.start - qs.count(),
                          index.stop - qs.count())
            if index.start < 0:
                if index.stop < 0:
                    break
                index = slice(0, index.stop)
        if multi:
            return (item for item in result)
        else:
            return result[0]

    def __iter__(self):
        for qs in self.querysets:
            for item in qs:
                yield item

    def count(self):
        result = 0
        for qs in self.querysets:
            result += qs.count()
        return result

    def __len__(self):
        return self.count()
