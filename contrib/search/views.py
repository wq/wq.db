from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework import status
from wq.db.rest.views import SimpleView

from .util import search
from .serializers import SearchResultSerializer

SEARCH_PARAMETER = 'q'


class SearchView(SimpleView, GenericAPIView, ListModelMixin):
    auto = False
    search = None
    content_type = None
    authority_id = None
    serializer_class = SearchResultSerializer

    def get_queryset(self):
        if not self.search:
            return []
        return search(
            self.search,
            self.auto,
            self.content_type,
            self.authority_id
        )

    def filter_queryset(self, queryset):
        return queryset

    def get(self, request, *args, **kwargs):
        self.search = request.GET.get(SEARCH_PARAMETER, None)
        self.auto = request.GET.get('auto', self.auto)
        self.content_type = request.GET.get('type', self.content_type)
        self.authority_id = request.GET.get('authority_id', self.authority_id)
        response = self.list(request, args, kwargs)

        if response.data['count'] == 1 and self.auto:
            return self.auto_redirect(response)
        else:
            return response

    def auto_redirect(self, response):
        item = response.data['list'][0]
        return Response(
            status=status.HTTP_302_FOUND,
            data={'message': 'Found', 'search': self.search},
            headers={'Location': '/' + item['url']}
        )


class DisambiguateView(SearchView):
    def get(self, request, *args, **kwargs):
        self.search = kwargs['slug']
        response = self.list(request, *args, **kwargs)
        if response.data['count'] == 0:
            raise Http404("Could not find %s", self.search)
        elif response.data['count'] == 1:
            return self.auto_redirect(response)
        else:
            response.data['message'] = "Multiple Matches Found"
            return response
