from django.conf.urls import url
from django.conf import settings

from .views import SearchView, DisambiguateView

urlpatterns = [
    url('^search/?$', SearchView.as_view()),
    url('^search\.(?P<format>\w+)$', SearchView.as_view()),
]

if getattr(settings, 'DISAMBIGUATE', False):
    urlpatterns += [
        url('^(?P<slug>[^\/]+)$', DisambiguateView.as_view()),
    ]
