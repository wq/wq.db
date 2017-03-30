from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict
from rest_framework.response import Response


class Pagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'limit'

    def paginate_queryset(self, queryset, request, view=None):
        data = super(Pagination, self).paginate_queryset(
            queryset, request, view
        )
        if not view or not view.router:
            return data

        if request.accepted_renderer.format != 'json':
            return data

        non_format_kwargs = [
            kwarg for kwarg in
            list(view.kwargs.keys()) + list(request.GET.keys())
            if kwarg != 'format'
        ]
        if view.action != 'list' or any(non_format_kwargs):
            return data

        conf = view.router.get_model_config(queryset.model)
        cache = conf.get('cache', 'first_page')

        if cache == 'first_page':
            return data
        elif cache == 'all':
            return list(queryset)
        elif cache == 'none':
            return []
        elif cache == 'filter':
            cache_filter = view.router.get_cache_filter_for_model(
                queryset.model
            )
            return list(cache_filter(queryset, self.request))

        return data

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            # DRF default metadata
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),

            # wq.db additional metadata
            ('page', self.page.number),
            ('pages', self.page.paginator.num_pages),
            ('per_page', self.page.paginator.per_page),
            ('multiple', self.page.paginator.num_pages > 1),

            # Actual data ('results' in DRF)
            ('list', data)
        ]))
