from django.http import Http404
from wq.db.rest.views import ModelViewSet


class IdentifiedModelViewSet(ModelViewSet):
    def get_object(self):
        try:
            obj = super(ModelViewSet, self).get_object()
        except Http404 as notfound:
            # Allow retrieval via non-primary identifiers
            slug = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)
            try:
                obj = self.model.objects.get_by_identifier(slug)
            except self.model.DoesNotExist:
                raise notfound
            # TODO: automatically redirect to primary identifier?
        return obj
