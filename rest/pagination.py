from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict
from rest_framework.response import Response


class Pagination(PageNumberPagination):
    page_size_query_param = 'limit'

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
