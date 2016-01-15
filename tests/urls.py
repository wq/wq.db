from django.conf.urls import patterns, include, url
from wq.db import rest

from tests.test_relate import create_reltype
create_reltype()

urlpatterns = patterns(
    '',
    url(r'^',        include(rest.router.urls)),
    url(r'^search/', include('wq.db.contrib.search.urls')),
)
