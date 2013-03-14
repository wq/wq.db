from wq.db.rest.views import View, PaginatorMixin
from rest_framework import status, response
from wq.db.rest import util
from .resources import SearchResource

SEARCH_PARAMETER = 'q'

class SearchView(PaginatorMixin, View):
    resource = SearchResource
    auto = False
    search = None
        
    def get(self, request, *args, **kwargs):
        self.search = request.GET.get(SEARCH_PARAMETER, None)
        self.auto = request.GET.get('auto', self.auto)
        if not self.search:
            return [] 

        results = self._resource.search(self.search, self.auto)
        if results.count() == 1 and self.auto:
            return self.auto_redirect(results[0])
        else:
            return results

    def auto_redirect(self, item):
        item = self._resource.serialize_model(item)
        return response.Response(
            status.HTTP_302_FOUND, 
            {'message': 'Found', 'search': self.search},
            {'Location': '/' + item['url']}
        )

    def filter_response(self, obj):
        if isinstance(obj, dict):
            return obj
        result = super(SearchView, self).filter_response(obj)
        result['list'] = result['results']
        del result['results']
        result['search'] = self.search
        return result


class DisambiguateView(SearchView):
    resource = SearchResource

    def get(self, request, *args, **kwargs):
        self.search = kwargs['slug']
        results = self._resource.search(self.search, True)
        if results.count() == 0:
            raise response.ErrorResponse(status.HTTP_404_NOT_FOUND, {
                'slug': self.search,
                'message': "Page Not Found"
            })
        elif results.count() == 1:
            return self.auto_redirect(results[0])
        return results

    def filter_response(self, obj):
        if isinstance(obj, dict):
            return obj
        result = super(DisambiguateView, self).filter_response(obj)
        result['message'] = "Multiple Matches Found"
        return result
