from djangorestframework.renderers import BaseRenderer, JSONRenderer, XMLRenderer
from djangorestframework import status
from pystache.renderer import Renderer as Mustache
from django.conf import settings
from wq.db.util import get_config, get_ct, get_id

mustache = Mustache(
    file_extension = 'html',
    search_dirs    = settings.TEMPLATE_DIRS
)

class RedirectRenderer(BaseRenderer):
    media_type = 'text/html'
    def render(self, obj=None, accept=None):
        path = self.view.request.path
        self.view.response.status = status.HTTP_302_FOUND
        self.view.response.headers['Location'] = '/#' + path
        return 'Redirecting...'

class MustacheRenderer(BaseRenderer):
    media_type = 'text/html'
    def render(self, obj=None, accept=None):
        user   = self.view.request.user
        config = get_config(user)
        ctid   = get_id(get_ct(self.view.resource.model))
        parts  = self.view.request.path.split('/')
        if isinstance(obj, list):
            template = ctid + '_list'
            context  = {'list': obj}
        else:
            template = ctid + '_detail'
            context  = obj
        if user.is_authenticated():
            context['user'] = {
                key: getattr(user, key)
                for key in ('username', 'first_name', 'last_name', 'email', 
                            'is_active', 'is_staff', 'is_superuser')
            }
        template = mustache.load_template(template)
        return mustache.render(template, context)

if getattr(settings, 'RENDER_ON_SERVER', False):
    HTMLRenderer = MustacheRenderer
else:
    HTMLRenderer = RedirectRenderer
