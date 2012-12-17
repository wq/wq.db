from django.conf.urls.defaults import patterns, include, url
from django.contrib.contenttypes.models import ContentType

from wq.db.rest import views, util

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

    listview, detailview = views.get_for_model(cls)
    urlbase = util.geturlbase(ct)

    urlpatterns += patterns('',
        url('^' + urlbase + r'/?$',  listview),
        url('^' + urlbase + r'\.(?P<format>\w+)$', listview),
        url('^' + urlbase + r'/new$', listview),
        url('^' + urlbase + r'/(?P<pk>[^\/\?]+)\.(?P<format>\w+)$', detailview),
        url('^' + urlbase + r'/(?P<pk>[^\/\?]+)/edit$', detailview),
        url('^' + urlbase + r'/(?P<pk>[^\/\?]+)/?$', detailview)
    )

    for pct in util.get_all_parents(ct):
        purl = '^' + util.geturlbase(pct) + r'/(?P<' + util.get_id(pct) + '>[^\/\?]+)/' + urlbase
        urlpatterns += patterns('',
            url(purl + '/?$', listview),
            url(purl + '\.(?P<format>\w+)$', listview),
        )

    for cct in util.get_all_children(ct):
        cbase = util.geturlbase(cct)
        curl = '^%s-by-%s'% (cbase, util.get_id(ct))
        kwargs = {'target': cbase}
        urlpatterns += patterns('',
            url(curl + '/?$', listview, kwargs),
            url(curl + '\.(?P<format>\w+)$', listview, kwargs),
        )
