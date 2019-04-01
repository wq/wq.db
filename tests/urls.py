try:
    from django.urls import path
except ImportError:
    from django.conf.urls import url
    path = None

from wq.db import rest
from tests.patterns_app.views import FilterableView
from .settings import WITH_NONROOT


if WITH_NONROOT:
    base_url = 'wqsite/'
else:
    base_url = ''


if path:
    urlpatterns = [
        path(base_url + 'filterable/<path:ids>', FilterableView.as_view()),
        path(base_url, rest.router.urls),
    ]
else:
    # FIXME: Remove in 2.0
    urlpatterns = [
        url(
            r'^' + base_url + 'filterable/(?P<ids>.+)',
            FilterableView.as_view()
        ),
        url(r'^' + base_url, rest.router.urls),
    ]
