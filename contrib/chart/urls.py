from django.conf.urls import patterns, include, url
from rest_framework.urlpatterns import format_suffix_patterns

ids = r'^(?P<ids>[^\.]+)'


def make_urls(views):
    urls = [
        url(ids + r'/' + name + '$', cls.as_view())
        for name, cls in views.items()
    ]
    return format_suffix_patterns(patterns('', *urls))
