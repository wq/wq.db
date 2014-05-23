from django.conf.urls import patterns, include, url
from rest_framework.urlpatterns import format_suffix_patterns
from .views import TimeSeriesView, ScatterView, BoxPlotView

ids = r'^(?P<ids>[^\.]+)'

urlpatterns = patterns('',
    url(ids + r'/timeseries$', TimeSeriesView.as_view()),
    url(ids + r'/scatter$', ScatterView.as_view()),
    url(ids + r'/boxplot$', BoxPlotView.as_view()),
)
urlpatterns = format_suffix_patterns(urlpatterns)
