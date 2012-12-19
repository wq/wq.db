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

class MustacheRenderer(BaseRenderer):
    media_type = 'text/html'
    file_extension = 'html'
    def render(self, obj=None, accept=None):
        user   = self.view.request.user
        config = get_config(user)
        template = self.view.template

        if obj:
            if user.is_authenticated():
                obj['user'] = user_dict(user)
            if 'list' in obj and 'pages' in obj:
                obj['multiple'] = (obj['pages'] > 1)

        if not hasattr(self, '_mustache'):
            self._mustache = Mustache(
                file_extension = self.file_extension,
                search_dirs    = dirs
            )

        template = self._mustache.load_template(self.view.template)
        return self._mustache.render(template, obj)

class AMDRenderer(JSONPRenderer):
    media_type = 'application/javascript'
    format = 'js'
    callback_parameter = 'define'

if getattr(settings, 'RENDER_ON_SERVER', False):
    HTMLRenderer = MustacheRenderer
else:
    HTMLRenderer = RedirectRenderer
