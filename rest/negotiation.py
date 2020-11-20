from rest_framework.negotiation import DefaultContentNegotiation


JSON = 'application/json'
GEOJSON = 'application/geo+json'


class ContentNegotiation(DefaultContentNegotiation):
    """
    Some clients (such as Mapbox GL) might only Accept: application/json
    """
    def filter_renderers(self, renderers, format):
        self._format = format
        return super().filter_renderers(renderers, format)

    def get_accept_list(self, request):
        accepts = super().get_accept_list(request)
        if getattr(self, '_format', None) == 'geojson':
            if JSON in accepts and GEOJSON not in accepts:
                accepts.append(GEOJSON)
        return accepts
