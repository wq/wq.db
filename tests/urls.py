try:
    from django.urls import include, path
except ImportError:
    from django.conf.urls import include, url
    path = None

from wq.db import rest
from tests.patterns_app.views import FilterableView


if path:
    urlpatterns = [
        path('filterable/<path:ids>', FilterableView.as_view()),
        path('', include(rest.router.urls)),
    ]
else:
    urlpatterns = [
        url(r'^filterable/(?P<ids>.+)', FilterableView.as_view()),
        url(r'^', include(rest.router.urls)),
    ]
