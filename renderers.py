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
        config = get_config(self.view.request.user)
        ctid   = get_id(get_ct(self.view.resource.model))
        parts  = self.view.request.path.split('/')
        if len(parts) > 2 and len(parts[1]) > 0:
            template = ctid + '_detail'
            context  = obj
        else:
            template = ctid + '_list'
            context  = {'list': obj}
        template = mustache.load_template(template)
        return mustache.render(template, context)

if getattr(settings, 'RENDER_ON_SERVER', False):
    HTMLRenderer = MustacheRenderer
else:
    HTMLRenderer = RedirectRenderer
