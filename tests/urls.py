from django.conf.urls import include, url
from wq.db import rest

from tests.test_relate import create_reltype
create_reltype()

urlpatterns = [
    url(r'^',        include(rest.router.urls)),
    url(r'^search/', include('wq.db.contrib.search.urls')),
]
