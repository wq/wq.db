from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

from .views import SearchView, DisambiguateView

urlpatterns = patterns('',
    url('^search/?$',                SearchView.as_view()),
    url('^search\.(?P<format>\w+)$', SearchView.as_view())
)

if 'wq.db.identify' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url('^(?P<slug>[^\/]+)$', DisambiguateView.as_view())
    )
