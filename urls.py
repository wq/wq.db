from django.conf.urls.defaults import patterns, include, url

from django.contrib.contenttypes.models import ContentType

from wq.db import resources, views, util

urlpatterns = patterns('', 
    url('^config/?$',                views.ConfigView.as_view()),
    url('^config\.(?P<format>\w+)$', views.ConfigView.as_view()),
    url('^login/?$',                 views.LoginView.as_view()),
    url('^login\.(?P<format>\w+)$',  views.LoginView.as_view()),
    url('^logout/?$',                views.LogoutView.as_view()),
    url('^logout\.(?P<format>\w+)$', views.LogoutView.as_view()),
)

for ct in ContentType.objects.all():
        
    cls = ct.model_class()
    if cls is None:
        continue

    res        = resources.get_for_model(cls)
    listview   = views.ListOrCreateModelView.as_view(resource=res)
    detailview = views.InstanceModelView.as_view(resource=res)
    urlbase    = util.geturlbase(ct)

    urlpatterns += patterns('', url('^' + urlbase + r'/?$',  listview))
    urlpatterns += patterns('', url('^' + urlbase + r'\.(?P<format>\w+)$', listview))
    urlpatterns += patterns('', url('^' + urlbase + r'/new$', listview))
    urlpatterns += patterns('', url('^' + urlbase + r'/(?P<pk>[^\/\?]+)\.(?P<format>\w+)$', detailview))
    urlpatterns += patterns('', url('^' + urlbase + r'/(?P<pk>[^\/\?]+)/?$', detailview))

urlpatterns += patterns('',
    url('^(?P<slug>[^\/]+)$', views.DisambiguateView.as_view())
)
