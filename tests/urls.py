from django.conf.urls import patterns, include, url
from wq.db import rest
from wq.db.contrib.chart.urls import make_urls
from tests.chart_app import views

from tests.test_relate import create_reltype
create_reltype()

chart_urls = make_urls({
    'timeseries': views.TimeSeriesView,
    'scatter': views.ScatterView,
    'boxplot': views.BoxPlotView,
})

rest.autodiscover()
urlpatterns = patterns(
    '',
    url(r'^',       include(rest.router.urls)),
    url(r'^chart',  include(chart_urls)),
    url(r'^search/', include('wq.db.contrib.search.urls')),
)
