from django.conf.urls.defaults import patterns, include, url
from .views import LoginView, LogoutView
from wq.db.rest.util import add_page_config

urlpatterns = patterns('', 
    url('^login/?$',                 LoginView.as_view()),
    url('^login\.(?P<format>\w+)$',  LoginView.as_view()),
    url('^logout/?$',                LogoutView.as_view()),
    url('^logout\.(?P<format>\w+)$', LogoutView.as_view()),
)

add_page_config('login',  {'name': 'Log in',  'url': 'login'})
add_page_config('logout', {'name': 'Log out', 'url': 'logout'})
