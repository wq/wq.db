from django.conf.urls import patterns, url

from wq.db.rest import app
from .views import GenerateView

urlpatterns = patterns('',
    url(r'^generate/(?P<size>\d+)/(?P<image>.+)$', GenerateView.as_view()),
)
