from djangorestframework.renderers import (BaseRenderer,
     JSONRenderer, JSONPRenderer, XMLRenderer)
from djangorestframework import status
from pystache.renderer import Renderer as Mustache
from django.conf import settings
from wq.db.rest.util import get_config, get_ct, get_id, user_dict

dirs = []
for d in settings.TEMPLATE_DIRS:
    dirs.append(d)
    dirs.append(d + '/partials')

class RedirectRenderer(BaseRenderer):
    media_type = 'text/html'
    def render(self, obj=None, accept=None):
        path = self.view.response.headers.get('Location', self.view.request.path)
        query = self.view.request.GET.urlencode()
        if query:
            path += "?" + query
        self.view.response.status = status.HTTP_302_FOUND
        self.view.response.headers['Location'] = '/#' + path
        return 'Redirecting...'

    @staticmethod
    def register_context_default(name, val):
        pass

class MustacheRenderer(BaseRenderer):
    media_type = 'text/html'
    file_extension = 'html'
    _defaults = {}

    def render(self, obj=None, accept=None):
        template = self.view.template

        if obj is None:
            obj = {}
        for name, val in MustacheRenderer._defaults.items():
            if name not in obj:
                if callable(val):
                    val = val(self, obj)
                if val is not None:
                    obj[name] = val

        if not hasattr(self, '_mustache'):
            self._mustache = Mustache(
                file_extension = self.file_extension,
                search_dirs    = dirs
            )

        template = self._mustache.load_template(self.view.template)
        return self._mustache.render(template, obj)

    @staticmethod
    def register_context_default(name, val):
        MustacheRenderer._defaults[name] = val

class AMDRenderer(JSONPRenderer):
    media_type = 'application/javascript'
    format = 'js'
    callback_parameter = 'define'

if getattr(settings, 'RENDER_ON_SERVER', False):
    HTMLRenderer = MustacheRenderer
else:
    HTMLRenderer = RedirectRenderer
