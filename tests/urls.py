from django.conf.urls import patterns, include, url
from wq.db.rest import app
from wq.db.contrib.chart.urls import make_urls
from tests.chart_app import views

chart_urls = make_urls({
    'timeseries': views.TimeSeriesView,
    'scatter': views.ScatterView,
    'boxplot': views.BoxPlotView,
})

app.autodiscover()
urlpatterns = patterns('',
    url(r'^',       include(app.router.urls)),
    url(r'^chart',  include(chart_urls)),
)
