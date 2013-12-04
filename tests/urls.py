from django.conf.urls import patterns, include, url
from wq.db.rest import app
app.autodiscover()
app.router.add_page('index', {'url': ''})
urlpatterns = patterns('',
    url(r'^',       include(app.router.urls))
)
