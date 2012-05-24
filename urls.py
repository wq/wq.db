from django.conf.urls.defaults import patterns, include, url

from django.contrib.contenttypes.models import ContentType

from wq.db import resources, views

urlpatterns = patterns('', 
    url('^config$', views.Config.as_view())
)

for ct in ContentType.objects.all():
    cls = ct.model_class()
    if cls is None:
        continue

    res        = resources.get_for_model(cls)
    listview   = views.ListOrCreateModelView.as_view(resource=res)
    detailview = views.InstanceModelView.as_view(resource=res)
    urlbase    = views.geturlbase(ct)

    urlpatterns += patterns('', url(urlbase + r'/$', listview))
    urlpatterns += patterns('', url(urlbase + r'/new$', listview))
    urlpatterns += patterns('', url(urlbase + r'/(?P<pk>[^/]+)', detailview))
