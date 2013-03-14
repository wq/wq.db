from django.conf.urls.defaults import patterns, include, url
from .views import LoginView, LogoutView

urlpatterns = patterns('', 
    url('^login/?$',                 LoginView.as_view()),
    url('^login\.(?P<format>\w+)$',  LoginView.as_view()),
    url('^logout/?$',                LogoutView.as_view()),
    url('^logout\.(?P<format>\w+)$', LogoutView.as_view()),
)
